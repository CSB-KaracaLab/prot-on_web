import pandas as pd
from flask import Flask, render_template,send_from_directory,redirect,url_for,flash,request,send_file
import os, time
from dotenv import load_dotenv
from celery import Celery
from alert import Alerts
from detect_outliers import main_DO
from interface_residues import main_IR
from energy_calculation_EvoEF import main_EvoEF
from energy_calculation_FoldX import main_FoldX
import shutil
from celery.schedules import crontab
from celery.utils.log import get_task_logger
from flask_mail import Mail, Message
import plotly
import plotly.graph_objects as go
import plotly.express as px
import json
import task
from werkzeug.utils import secure_filename
import urllib.request
import uuid
import numpy as np

load_dotenv()
logger = get_task_logger(__name__)
hostname = os.system("hostname -I") #or type your domain as a string 

def make_celery(app):
    celery = Celery(
        app.import_name,
        backend=app.config["CELERY_BACKEND_URL"],
        broker=app.config["CELERY_BROKER_URL"],
        broker_connection_retry_on_startup = True
    )
    celery.conf.update(app.config)
    
    
    class ContextTask(celery.Task):
        def __call__(self, *args, **kwargs):
            with app.app_context():
                return self.run(*args, **kwargs)

    celery.Task = ContextTask
    return celery

flask_app = Flask(__name__)
flask_app.config.update(
    CELERY_BROKER_URL=os.environ.get("CELERY_BROKER_URL"),
    CELERY_BACKEND_URL=os.environ.get("CELERY_BACKEND_URL"),
    SECRET_KEY = os.environ.get("SECRET_KEY"), #Fill your secret key
    MAIL_SERVER = "smtp-relay.gmail.com", #Fill with your mail server
    MAIL_PORT = 587, #Type your mail port. Please contact with your mail server.
    MAIL_USE_TLS = True,
    MAIL_USERNAME = "proton.tools@ibg.edu.tr", #Fill with your e-mail here
    MAIL_DEFAULT_SENDER = "proton.tools@ibg.edu.tr", #Fill with your e-mail here
    worker_concurrency = 1, #How many jobs will be run at the same time?
    beat_schedule = {
        # Executes every night
        'periodic_task-every-night': {
            'task': 'periodic_task',
            'schedule': crontab(minute=0, hour=0)
        },
    }
)

mail= Mail(flask_app)
celery = make_celery(flask_app)

#upload pdb files
UPLOAD_FOLDER = ""
ALLOWED_EXTENSIONS = {'pdb'}
flask_app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
downloadurl="https://files.rcsb.org/download/"

@flask_app.route("/")
def index():
    return render_template("index.html")

@flask_app.route("/new-run")
def new_run():
    return render_template("index.html")

#add favicon icon
@flask_app.route("/favicon.ico")
def favicon():
    return send_from_directory(os.path.join(flask_app.root_path, "static"),
    "favicon.ico",mimetype = "image/vnd.microsoft.icon")

@celery.task(name ="periodic_task")
def periodic_task():
    path = "run_results/"
    now = time.time()
    
    for filename in os.listdir(path):
        filestamp = os.stat(os.path.join(path, filename)).st_mtime
        filecompare = now - 7 * 86400
        if  filestamp < filecompare:
            if filename == "ACE2_RBD_EvoEF1":
                pass
            elif filename == "MCL1_NOXA_FoldX":
                pass
            elif filename == "MDM2_p53_EvoEF1":
                pass
            elif filename == "MDM2_p53_FoldX":
                pass
            elif filename == "1JPS_HeavyChain_TissueFactor":
                pass
            elif filename == "1JPS_LightChain_TissueFactor":
                pass
            elif filename == "dae4ee4df0ec47e9a119fd512fdbfd98":
                pass
            elif filename == "73cdda1fade6457faefa98af9e55b454":
                pass
            elif filename == "5ab290262ad340eaba0e6357b6ef46f2":
                pass
            else:
                os.system("rm -rf {}".format(path+filename))

    logger.info("Periodic run deletion initiated!")

@celery.task
def proton(chain_1,chain_2,selected_chain,cut_off,iqr,algorithm,protein_structure,pssm,run_id,email,name):
    os.chdir(run_id)
    shutil.copy(protein_structure, "..")
    os.remove(protein_structure)
    if pssm != "":
        shutil.copy(pssm, "..")
        os.remove(pssm)
    os.chdir("..")
    pdb = protein_structure[:-4]
    os.mkdir("{}_chain_{}_{}_output".format(pdb,selected_chain,algorithm))
    main_IR(protein_structure,chain_1,chain_2,selected_chain,cut_off)
    if algorithm == "FoldX":
        main_FoldX(protein_structure,selected_chain)
    else:
        main_EvoEF(protein_structure,selected_chain,algorithm)
    main_DO(protein_structure,selected_chain,algorithm,pssm,cut_off,iqr)
    shutil.move(UPLOAD_FOLDER + "heatmap_df", "{}_chain_{}_{}_output".format(pdb,selected_chain,algorithm))
    shutil.move(UPLOAD_FOLDER + protein_structure, "{}_chain_{}_{}_output".format(pdb,selected_chain,algorithm))
    shutil.move(UPLOAD_FOLDER + "{}_pairwise_distance_list".format(pdb), "{}_chain_{}_{}_output".format(pdb,selected_chain,algorithm))
    shutil.move(UPLOAD_FOLDER + "{}_chain_{}_interface_aa_list".format(pdb,selected_chain), "{}_chain_{}_{}_output".format(pdb,selected_chain,algorithm))
    shutil.move(UPLOAD_FOLDER + "{}_chain_{}_proton_scores".format(pdb,selected_chain), "{}_chain_{}_{}_output".format(pdb,selected_chain,algorithm))
    shutil.move(UPLOAD_FOLDER + "{}_chain_{}_mutation_list".format(pdb,selected_chain), "{}_chain_{}_{}_output".format(pdb,selected_chain,algorithm))
    os.remove(UPLOAD_FOLDER + "heatmap_mutation_list")
    os.system("rm *.pdb")
    os.chdir(UPLOAD_FOLDER + "{}_chain_{}_{}_output".format(pdb,selected_chain,algorithm))
    parameters = open("parameters","w")
    print("cut_off:{}   iqr:{}".format(cut_off,iqr), file = parameters)
    parameters.close()
    os.system("cp ../output_README .".format())
    os.system("tar cvzf {}_chain_{}_{}_output.tar.gz *".format(pdb,selected_chain,algorithm))
    mutations = []
    for i in os.listdir("mutation_models"):
        mutations.append(i)
    os.chdir("../")
    shutil.move(UPLOAD_FOLDER + "{}_chain_{}_{}_output".format(pdb,selected_chain,algorithm), run_id)
    shutil.move(UPLOAD_FOLDER + run_id, "run_results")
    id = os.system("whoami")
    os.system("chown {}:{} run_results/{}/{}_chain_{}_{}_output".format(id,id,run_id,pdb,selected_chain,algorithm))
    os.system("chown {}:{} run_results/{}/{}_chain_{}_{}_output/mutation_models/*".format(id,id,run_id,pdb,selected_chain,algorithm))
    os.system("chown {}:{} run_results/{}".format(id,id,run_id))
    os.system("chown {}:{} run_results/{}/{}_chain_{}_{}_output/*".format(id,id,run_id,pdb,selected_chain,algorithm))
    SendMail(email,name,run_id)

def SendMail(email,name,run_id):
    msg = Message("PROT-ON Run Results", sender = "proton.tools@ibg.edu.tr", recipients=[email]) #Fill with your e-mail here
    msg.body = ("""
    Thank you for using PROT-ON. Your {} run is now complete. You can access run results at http://{}/result/{}. Your result will be accessible for a week.
    """.format(hostname,name,run_id)) 
    if email != "":
        mail.send(msg)
    else:
        pass

@flask_app.route("/feedback", methods=["GET","POST"])
def feedback():
    if request.method == "POST":
        email = request.form.get("email_feedback")
        name = request.form.get("feedback_name")
        send_email = "proton.tools@ibg.edu.tr" #Fill with your e-mail here
        message = request.form.get("message")
        subject = request.form.get("subject")
        msg = Message(subject, sender = "proton.tools@ibg.edu.tr", recipients=[send_email]) #Fill with your e-mail here
        msg.body = """WE HAVE RECEIVED A FEEDBACK!
         Sender Name: {} 
         Sender Email: {}
         Feedback: {}""".format(name,email,message)
        mail.send(msg)
        return redirect(url_for('new_run'))
    return render_template("index.html")

def Check(chain_1,chain_2,selected_chain,protein_structure,pssm,cut_off):
    a = Alerts(protein_structure,chain_1,chain_2,selected_chain,pssm,cut_off)
    if a.nameAlert() is False:
        flash("Please refrain from using '.' in file naming","danger")
        return redirect(url_for("new_run"))
    elif a.Chain_Alert() is False:
        flash("Please check the chain IDs","danger")
        return redirect(url_for("new_run"))
    elif a.Chain_on_Alert() is False:
        flash("Please reload the homepage and check the chain ID button to be analyzed.","danger")
        return redirect(url_for("new_run"))
    elif a.PSSM_Alert() is False:
        flash("Please check the PSSM file","danger")
        return redirect(url_for("new_run"))
    elif a.Cut_off_Alert() is False:
        flash("There are no interacting residues within that cut-off","danger")
        return redirect(url_for("new_run"))
    else:
        return True

@flask_app.route("/result/<run_id>",  methods=["GET","POST"])
def ResultPage(run_id):
    if request.method == "GET":
        try:
            my_list = os.listdir(UPLOAD_FOLDER + "run_results/{}".format(run_id))
            splitting = my_list[0].split("_")
            algorithm = splitting[-2]
            chain = splitting[-3]
            for file in os.listdir("run_results/{}/{}".format(run_id,my_list[0])):
                if file .endswith(".pdb"):
                    pdb = file[:-4]
            os.chdir(UPLOAD_FOLDER + "run_results/{}/{}".format(run_id,my_list[0]))
            with open("parameters","r") as file:
                for line in file:
                    iqr = float(line[18:21])
                    cut_off = float(line[8:11])
            Scores_File = pd.read_table("{}_chain_{}_proton_scores".format(pdb,chain), sep = " ")
            heatmap = pd.read_table("heatmap_df",sep = " ")
            depleting = pd.read_table("{}_chain_{}_depleting_mutations".format(pdb,chain), sep=" ")
            enriching = pd.read_table("{}_chain_{}_enriching_mutations".format(pdb,chain), sep=" ")
            num_out = len(depleting) + len(enriching)
            try:
                DM_DF = pd.read_table("{}_chain_{}_pssm_depleting".format(pdb,chain), sep = " ")
                DM_List = DM_DF.values.tolist()
                EM_DF = pd.read_table("{}_chain_{}_pssm_enriching".format(pdb,chain), sep = " ")
                EM_List = EM_DF.values.tolist()
                NumDep = int(len(DM_DF["Positions"]))
                NumEnr = int(len(EM_DF["Positions"]))                
                col=DM_DF.shape[1]
            except:
                DM_DF = pd.read_table("{}_chain_{}_depleting_mutations".format(pdb,chain), sep = " ")
                EM_DF = pd.read_table("{}_chain_{}_enriching_mutations".format(pdb,chain), sep = " ")
                DM_List = DM_DF.values.tolist()
                EM_List = EM_DF.values.tolist()
                NumDep = int(len(DM_DF["Positions"]))
                NumEnr = int(len(EM_DF["Positions"]))
                col=DM_DF.shape[1]
            TMPosition = Scores_File.groupby(['Positions'])['DDG_{}_Scores'.format(algorithm)].mean()
            TMPosition_DM = TMPosition.idxmax()
            TMPosition_EM = TMPosition.idxmin()
            NumInterfacialAA = int(len(Scores_File["Positions"]) / 19)
            try:
                idxmax_DM = DM_DF["DDG_{}_Scores".format(algorithm)].idxmax()
                max_DM = DM_DF["DDG_{}_Scores".format(algorithm)].max()
                PDM = DM_DF["Positions"].iloc[idxmax_DM]
                MDM = DM_DF["Mutations"].iloc[idxmax_DM]
                TMD = PDM + MDM
            except:
                max_DM = None
                TMD = None
            try:
                idxmin_EM = EM_DF["DDG_{}_Scores".format(algorithm)].idxmin()
                min_EM = EM_DF["DDG_{}_Scores".format(algorithm)].min()
                PEM = EM_DF["Positions"].iloc[idxmin_EM]
                MEM = EM_DF["Mutations"].iloc[idxmin_EM]
                TME = PEM + MEM
            except:
                min_EM = None
                TME = None
            DDG_Scores = list(Scores_File["DDG_{}_Scores".format(algorithm)])
            q1 = np.quantile(DDG_Scores,0.25)
            q3 = np.quantile(DDG_Scores, 0.75)
            IQR = float(q3 - q1)
            upperfence = q3 + (iqr * IQR)
            lowerfence = q1 - (iqr * IQR)
            for i in DDG_Scores:
                if i < lowerfence:
                    negative_outlier = q1 - (iqr * IQR)
                    break
                else:
                    negative_outlier = min(DDG_Scores)
            
            for i in DDG_Scores:
                if i > upperfence:
                    positive_outlier = q3 + (iqr * IQR)
                    break
                else:
                    positive_outlier = max(DDG_Scores)
            boxplot = go.Figure()
            boxplot.add_trace(go.Box(y=[DDG_Scores],boxpoints="outliers",hovertemplate='<b>ΔΔG Score</b>: %{y}<extra></extra>'))
            boxplot.update_traces(q1=[np.quantile(DDG_Scores,0.25)], 
                median=[np.quantile(DDG_Scores,0.50)],
                q3=[np.quantile(DDG_Scores,0.75)],
                lowerfence=[negative_outlier],
                upperfence=[positive_outlier])
            boxplot.update_layout(title="<b>Distribution of {} ΔΔG Scores</b>".format(algorithm),
                title_x=0.5,
                yaxis={"title": '<b>{} ΔΔG Scores</b>'.format(algorithm)},
                template="plotly_white",
                width=430, height=650)
            boxplot.update_yaxes(tickprefix="<b>",ticksuffix ="</b><br>")
            boxplotJSON = json.dumps(boxplot, cls=plotly.utils.PlotlyJSONEncoder)
            mid = float(0 - heatmap["DDG_{}_Scores".format(algorithm)].min() / (heatmap["DDG_{}_Scores".format(algorithm)].max() - heatmap["DDG_{}_Scores".format(algorithm)].min()))
            colorscale = [[0, 'rgba(0, 102, 170, 255)'],
            [mid, 'rgba(255, 255, 255, 0.85)'],
            [1, 'rgba(214, 39, 40, 0.85)']]
            fig = go.Figure(go.Heatmap(colorbar={"title": "<b>ΔΔG {} Scores</b>".format(algorithm)},
                z=Scores_File["DDG_{}_Scores".format(algorithm)],
                x=Scores_File["Mutations"],
                y=Scores_File["Positions"],
                colorscale=colorscale,
                zmin=negative_outlier,
                zmax=positive_outlier,
                hovertemplate='Mutation: %{x}<br>Position: %{y}<br>ΔΔG: %{z}<extra></extra>'))
            fig.update_layout(title="<b>Heatmap for chain {} of {}</b>".format(chain,pdb),
                title_x=0.5,
                yaxis={"title": '<b>Positions</b>'},
                xaxis={"title": '<b>Mutations</b>'},
                yaxis_nticks=len(Scores_File["Positions"]),
                width=650, height=650)
            fig.update_xaxes(tickprefix="<b>",ticksuffix="</b><br>")
            graphJSON = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)
            PositionSpecificBP = px.box(Scores_File, x="Positions", y="DDG_{}_Scores".format(algorithm),color="Positions",hover_data=["Mutations"],template="plotly_white")
            PositionSpecificBP.update_layout(title="<b>Position Specific Distribution of {} ΔΔG Scores</b>".format(algorithm),
                title_x=0.5,
                xaxis={"title": '<b>Positions</b>'},
                yaxis={"title": '<b>{} ΔΔG Scores</b>'.format(algorithm)},
                xaxis_nticks=len(Scores_File["Positions"]))
            PositionSpecificBP.update_yaxes(tickprefix="<b>",ticksuffix="</b><br>")
            PositionSpecificBP.update_xaxes(tickprefix="<b>",ticksuffix="</b><br>")
            PositionSpecificBPJSON = json.dumps(PositionSpecificBP, cls=plotly.utils.PlotlyJSONEncoder)
            os.chdir("../../../")
            return render_template("result.html", num_out=num_out,run_id=run_id,graphJSON=graphJSON,PositionSpecificBPJSON=PositionSpecificBPJSON,boxplotJSON=boxplotJSON,pdb=pdb,NumInterfacialAA=NumInterfacialAA,algorithm=algorithm,NumDep=NumDep,NumEnr=NumEnr,max_DM=max_DM,TMD=TMD,min_EM=min_EM,TME=TME,TMPosition_DM=TMPosition_DM,TMPosition_EM=TMPosition_EM,DM_List=DM_List,EM_List=EM_List,len_DM=len(DM_List),len_EM=len(EM_List),col=col,iqr=iqr,cut_off=cut_off)
        except:
            return render_template("refresh.html")
    
@flask_app.route('/download/<run_id>', methods=["GET","POST"])
def download_run(run_id):
    if request.method == "GET":
        my_list = os.listdir(UPLOAD_FOLDER + "run_results/{}".format(run_id))
        splitting = my_list[0].split("_")
        algorithm = splitting[-2]
        chain = splitting[-3]
        for file in os.listdir("run_results/{}/{}".format(run_id,my_list[0])):
            if file .endswith(".pdb"):
                pdb = file[:-4]
        path = "run_results/{}/{}_chain_{}_{}_output/{}_chain_{}_{}_output.tar.gz".format(run_id,pdb,chain,algorithm,pdb,chain,algorithm)
        return send_file(path, as_attachment=True)

@flask_app.errorhandler(404)
def not_found_error(error):
    return render_template('404.html'),404

@flask_app.route("/new-run", methods=["GET","POST"])
def result():
    if request.method == "POST":
        name = request.form.get("run_name")
        chain_1 = request.form.get("chain_1")
        chain_2 = request.form.get("chain_2")
        selected_chain = request.form.get("select_chain")
        cut_off = float(request.form.get("cut_off"))
        iqr = float(request.form.get("iqr"))
        algorithm = "EvoEF1"
        pdb_id = request.form.get("pdb_id")
        email = request.form.get("email")
        run_id = str(uuid.uuid4().hex)
        pssm_file = request.files["pssm_file"]
        pssm = secure_filename(pssm_file.filename)
        if pdb_id is None:
            structure = request.files["structure"]
            protein_structure = secure_filename(structure.filename)
            structure.save(os.path.join(flask_app.config['UPLOAD_FOLDER'], protein_structure))
            if pssm != "":
                pssm_file.save(os.path.join(flask_app.config['UPLOAD_FOLDER'], pssm))
            if Check(chain_1,chain_2,selected_chain,protein_structure,pssm,cut_off) is True:  
                flash("Your run is queued. Please stay on this page.","success")
                os.mkdir(run_id)
                if pssm != "":
                    shutil.copy(pssm, UPLOAD_FOLDER + run_id)
                shutil.copy(protein_structure, UPLOAD_FOLDER + run_id)
                task.task(chain_1,chain_2,selected_chain,cut_off,iqr,algorithm,protein_structure,pssm,run_id,email,name)
                return redirect('http://{}/result/{}'.format(hostname,run_id))
        elif pdb_id != "":
            protein_structure = pdb_id + ".pdb"
            url = downloadurl + protein_structure
            try:
                urllib.request.urlretrieve(url, os.path.join(flask_app.config["UPLOAD_FOLDER"],protein_structure))
            except:
                flash("PROT-ON can only read PDB formatted files. It cannot read mmCIF format. Please check your input data.","danger")
                return redirect(url_for("new_run"))
            if pssm != "":
                pssm_file.save(os.path.join(flask_app.config['UPLOAD_FOLDER'], pssm))
            if Check(chain_1,chain_2,selected_chain,protein_structure,pssm,cut_off) is True:
                flash("Your run is queued. Please stay on this page","success")
                os.mkdir(run_id)
                if pssm != "":
                    shutil.copy(pssm, UPLOAD_FOLDER + run_id)
                shutil.copy(protein_structure, UPLOAD_FOLDER + run_id)
                task.task(chain_1,chain_2,selected_chain,cut_off,iqr,algorithm,protein_structure,pssm,run_id,email,name)
                return redirect('http://{}/result/{}'.format(hostname,run_id))
                
    return render_template("index.html", chain_1=chain_1,chain_2=chain_2,selected_chain=selected_chain,cut_off=cut_off,iqr=iqr,algorithm=algorithm,protein_structure=protein_structure,pssm=pssm,run_id=run_id,email=email,name=name)

@flask_app.route("/pre-calculated_runs")
def Pre_calculated_Runs_Page():
    return render_template("pre-calculated_runs.html")

@flask_app.route("/help")
def Help():
    return render_template("help.html")

@flask_app.route("/about")
def AboutPage():
    return render_template("about.html")

if __name__ == "__main__":
    flask_app.run(debug=True)
