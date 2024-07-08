### Deployment of the Server Step by Step

PROT-ON will deploy to your IP address after completing these instructions. If you prefer to deploy it on a specific domain/IP, please enter your domain/IP as a string in the `hostname` variable within `app.py` (PROT-ON's default domain is proton.tools.ibg.edu.tr:8001). You can also change the e-mail address to which the results are sent. For this, Please press `command/ctrl + f`, type `Fill with your e-mail here`, and edit with your e-mail in `app.py` script. Also if needed, you must change `MAIL_PORT`. 

If you want to deploy the server step by step, without using quick installation, please aplly followings.
#### EvoEF1 and FoldX Installation

`library` and `src` folders are necessary to obtain EvoEF executable file. Please do not change or delete any files in those folders. Firstly, run the following command to create EvoEF executable file.

for Linux:
```
g++ -O3 --fast-math -o EvoEF src/*.cpp
```

If you want to analyze your complex with FoldX, you need to move the FoldX executable script named `foldx` and the `rotabase.txt` file to the working directory.

#### Environment Setup

Create a virtual environment and install dependencies

```
python3 -m venv <environment-name-you-choose>
source <environment-name-you-choose>/bin/activate
pip install -r requirements.txt
```

#### Installation of RabbitMQ

RabbitMQ is a message broker application used to manage background tasks in the PROT-ON webserver. To download and install RabbitMQ, run the following command

To install RabbitMQ:
```
sudo apt-get install rabbitmq-server
```

To initate it:
```
sudo rabbitmq-server -detached
```

Now, you should configure the RabbitMQ server settings to create a new user on host server and set permissions.

```
sudo rabbitmqctl add_user <username> <password>
sudo rabbitmqctl add_vhost <hostname>
sudo rabbitmqctl set_permissions -p <hostname> <username> ".*" ".*" ".*"
```

#### Deployment of the Server with Nginx

Firstly, Gunicorn configuration is needed. Gunicorn is used to deploy the PROT-ON's Flask app on your localhost (PROT-ON listen 8001th port as a default).
```
gunicorn app:flask_app -b localhost:8000 &
```
You can configure the Gunicorn process to listen on any open port (You can terminate the terminal after this step). Running Gunicorn in the background will work fine for your purposes here. However, a better approach would be to run Gunicorn through Supervisor.

Supervisor allows you to monitor and control multiple processes on UNIX-like operating systems. It will oversee the Gunicorn process, ensuring it restarts if something goes wrong or starts at boot time.

To install supervisor:
```
sudo apt-get install supervisor
```
Then, create a Supervisor configuration file (like proton.conf) at `/etc/supervisor/conf.d/` and configure it according to your requirements Before configuration, you must create `prot-on` folder under `/var/log` directory (PROT-ON listen 8001th port as a default).

```
[program:prot-on]
directory=/path/your/prot-on/directory
command=/path/your/prot-on/environment/bin/gunicorn app:flask_app -b localhost:8000
autostart=true
autorestart=true
stderr_logfile=/var/log/prot-on/prot-on.err.log
stdout_logfile=/var/log/prot-on/prot-on.out.log
```

Run the following commands to enable the configuration.

```
sudo supervisorctl reread
sudo service supervisor restart
```

**If you change/update anything on the server files/scripts, you must rerun below commands.** 

```
sudo service supervisor restart
```

After that, we need to deploy our service on a domain or IP address. First of all, Nginx must be downloaded:

To install:
```
sudo apt-get install nginx
```

Now, a server block must be established for the PROT-ON application

```
sudo nano /etc/nginx/conf.d/prot-on.conf
```

Then, paste the following configuration (PROT-ON listen 8001th port as a default)

```
server {
    listen       80;
    server_name  your_public_domain_here_or_ip_address;

    location / {
        proxy_pass http://127.0.0.1:8000;
    }
}
```

You must change `your_public_domain_here_or_ip_address;` with your domain or IP address (you can check your local IP address via *ifconfig* command)

The proxy pass directive should match the port on which the Gunicorn process is listening.

Restart the nginx web server.
```
sudo nginx -t
sudo service nginx restart
```

To check whether you deployed the PROT-ON successfully or not, please type your server name (the domain name or IP address) on your browser.

## Installation of Celery

Celery is a distributed task queue framework. It is used for handling asynchronous or scheduled tasks. It allows you to run and manage background jobs. Use the following command to install Celery (**You have to deactivate the environment to install and use the Celery**)

```
sudo apt-get install celery
```
Celery need to root access to run. In that case the Python dependencies of PROT-ON need to be installed with elevated privileges, so please ensure to use `sudo -H` parameter when downloading and installing them.

```
sudo -H pip3 install pandas
sudo -H pip3 install flask
sudo -H pip3 install python-dotenv
sudo -H pip3 install plotly
sudo -H pip3 install flask-mail
sudo -H pip3 install sqlalchemy
sudo -H pip3 install kaleido
sudo -H pip3 install numpy
```
You can start to use Celery in PROT-ON directory, after these installations.

#### To Run the PROT-ON Webserver

Before running the PROT-ON application, you must create an environment file named .env for Celery configuration. This file should includes user information for the RabbitMQ server, as shown below.
```
CELERY_BROKER_URL=amqp://<username>:<password>@localhost/<hostname>
CELERY_BACKEND_URL=db+sqlite:///proton.db
SECRET_KEY="YOUR_SECRET_KEY"
```

The last step, you must open two terminal tabs on PROT-ON working directory, and run following commands to initate background and scheduled tasks (You must run these commands at out of the environment), respectively. Note that, if any change or bugs occured in the scripts, please rerun them together with supervisor command below.

```
sudo celery -A app.celery worker --loglevel=info
sudo celery -A app.celery beat --loglevel=info
```

**If you encounter an internal error when you submit a run, you must reboot your system and run below commands again.**

### Citation

If you use the PROT-ON, please cite the following paper:
```
Koşaca, M., Yılmazbilek, İ., & Karaca, E. (2023).
PROT-ON: A structure-based detection of designer PROTein interface MutatiONs.
Frontiers in Molecular Biosciences, 10, 1063971.
```

### Bug Report & Feedback

If you encounter any problem, you can contact with Ezgi:

### Contacts

* ezgi.karaca@ibg.edu.tr
