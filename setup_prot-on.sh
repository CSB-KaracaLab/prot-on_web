#!/bin/bash

# Function to check for errors
check_error() {
    if [ $? -ne 0 ]; then
        echo "Error encountered. Exiting."
        exit 1
    fi
}
# Step 1: Create EvoEF executable file
echo "EvoEF executable file is creating..."
g++ -O3 --fast-math -o EvoEF src/*.cpp

# Step 2: Create a virtual environment and install dependencies
echo "Creating virtual environment and installing dependencies..."
read -p "Enter the name of the virtual environment: " VENV_NAME
python3 -m venv $VENV_NAME
check_error
source $VENV_NAME/bin/activate
check_error
pip install -r requirements.txt
check_error

# Step 3: Install RabbitMQ
echo "Installing RabbitMQ..."
sudo apt-get install -y rabbitmq-server
check_error

# Step 4: Start RabbitMQ server
echo "Starting RabbitMQ server..."
sudo rabbitmq-server -detached
check_error

# Step 5: Configure RabbitMQ
read -p "Enter RabbitMQ username: " RABBITMQ_USER
read -p "Enter RabbitMQ password: " RABBITMQ_PASS
read -p "Enter RabbitMQ virtual host: " RABBITMQ_VHOST

echo "Configuring RabbitMQ..."
sudo rabbitmqctl add_user $RABBITMQ_USER $RABBITMQ_PASS
check_error
sudo rabbitmqctl add_vhost $RABBITMQ_VHOST
check_error
sudo rabbitmqctl set_permissions -p $RABBITMQ_VHOST $RABBITMQ_USER ".*" ".*" ".*"
check_error

# Step 6: Install Supervisor
echo "Installing Supervisor..."
sudo apt-get install -y supervisor
check_error

# Step 7: Create Supervisor configuration file
SUPERVISOR_CONF="/etc/supervisor/conf.d/proton.conf"
read -p "Enter the path to your PROT-ON directory: " PROTON_DIR
read -p "Enter the path to your virtual environment: " VENV_DIR

echo "Creating Supervisor configuration file..."
sudo mkdir -p /var/log/prot-on
check_error

sudo tee $SUPERVISOR_CONF > /dev/null <<EOL
[program:prot-on]
directory=$PROTON_DIR
command=$VENV_DIR/bin/gunicorn app:flask_app -b localhost:8000
autostart=true
autorestart=true
stderr_logfile=/var/log/prot-on/prot-on.err.log
stdout_logfile=/var/log/prot-on/prot-on.out.log
EOL

# Step 8: Enable Supervisor configuration
echo "Enabling Supervisor configuration..."
sudo supervisorctl reread
check_error
sudo service supervisor restart
check_error

# Step 9: Install Nginx
echo "Installing Nginx..."
sudo apt-get install -y nginx
check_error

# Step 10: Configure Nginx
NGINX_CONF="/etc/nginx/conf.d/prot-on.conf"
read -p "Enter your public domain or IP address: " DOMAIN_OR_IP

echo "Creating Nginx configuration file..."
sudo tee $NGINX_CONF > /dev/null <<EOL
server {
    listen       80;
    server_name  $DOMAIN_OR_IP;

    location / {
        proxy_pass http://127.0.0.1:8000;
    }
}
EOL

# Step 11: Restart Nginx
echo "Restarting Nginx..."
sudo nginx -t
check_error
sudo service nginx restart
check_error

# Deactivate the virtual environment
echo "Deactivating the virtual environment..."
deactivate

# Step 12: Install Celery
echo "Installing Celery..."
sudo apt-get install -y celery
check_error

# Step 13: Install Python dependencies with elevated privileges
echo "Installing Python dependencies with elevated privileges..."
sudo -H pip3 install pandas flask python-dotenv plotly flask-mail sqlalchemy kaleido numpy
check_error

# Step 14: Create .env file for Celery configuration
ENV_FILE="$PROTON_DIR/.env"
read -p "Enter your secret key: " SECRET_KEY

echo "Creating .env file for Celery configuration..."
echo "CELERY_BROKER_URL=amqp://$RABBITMQ_USER:$RABBITMQ_PASS@localhost/$RABBITMQ_VHOST" > $ENV_FILE
echo "CELERY_BACKEND_URL=db+sqlite:///proton.db" >> $ENV_FILE
echo "SECRET_KEY=\"$SECRET_KEY\"" >> $ENV_FILE

# Update app.py with the provided IP address
APP_PY="$PROTON_DIR/app.py"
sed -i "s/hostname = .*/hostname = '$DOMAIN_OR_IP'/" $APP_PY

echo "Setup complete. Please reboot the system to verify the installation and configuration."
