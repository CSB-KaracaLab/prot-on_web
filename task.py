import app

def task(chain_1,chain_2,selected_chain,cut_off,iqr,algorithm,protein_structure,pssm,run_id,email,name):
    app.proton.apply_async((chain_1,chain_2,selected_chain,cut_off,iqr,algorithm,protein_structure,pssm,run_id,email,name))


