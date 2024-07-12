# Setup and Run Guide for Your Application

This guide provides detailed instructions on how to set up and run the application on an Ubuntu 20+ .

## Prerequisites
Before starting, ensure that you have the following software installed on your System:

1. Docker
2. Docker Compose
3. Git

If these are not installed, follow the steps below to install them.

## Step 1: Install Docker
### Update the package database:

sudo apt update

### Install prerequisite packages:

sudo apt install apt-transport-https ca-certificates curl software-properties-common -y

### Add Docker’s official GPG key:

curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo apt-key add -

### Add Docker repository:

sudo add-apt-repository "deb [arch=amd64] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable"


### Install Docker:

sudo apt update
sudo apt install docker-ce -y


### Start Docker and enable it to start on boot:

sudo systemctl start docker
sudo systemctl enable docker

## Step 2: Install Docker Compose
### Download the Docker Compose binary:

sudo curl -L "https://github.com/docker/compose/releases/download/1.29.2/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose

### Apply executable permissions to the binary:

sudo chmod +x /usr/local/bin/docker-compose

### Verify the installation:

docker-compose --version


## Step 3: Install Git
### Update the package database (if not already done):

sudo apt update

### Install Git:

sudo apt install git -y


## Step 4: Clone the Repository
### Navigate to the directory where you want to clone the repository:

cd /path/to/your/desired/folder

### Clone your repository:

git clone https://github.com/HORSE-EU-Project/Pre-Processing.git 

### Navigate into the cloned repository:

cd yourrepository


## Step 5: Set Up and Run the Application
### Run the docker-compose-services.yml file to set up the necessary services:

sudo docker-compose -f docker-compose-services.yml up -d

### Run the docker-compose.yml file to start the basic Flask application:

sudo docker-compose up -d

### Run the stanalone python application that manages ES data preprocessing & ditribution

sudo python3 ./ES_alert_system/main.py


## Step 6: Verify the Setup
### Check if all the containers are running:

sudo docker ps

### Access your application by navigating to the appropriate URL in your web browser. If your Flask application is running on port 5000, you can typically access it at:

http:// --your-vm-ip-- :5000

## Additional Tips
### To stop the containers, use:

docker-compose down

### To removing containers from VM
sudo docker rm --id of the container--

### To view the logs of a specific container, use:

docker logs --container_id--



# Setup Keycloak (for connection with Pre-Processing)
![image](https://github.com/user-attachments/assets/8bf1f591-9db9-4a85-8005-a243dc91d83c)

## Enter keycloak dashboard
in a browser --vm ip--:8080
Enter username (default: admin)
Enter password (default: admin)
Enter dashboard

## Create realm where every info about the users and apps are stored
Create a realm Called DFF and
### import DFF realm's imfo (by importing the json file)

### OR, create DFF realm manualy
Create a client "DFF" and generate a "Client Secret"
![image](https://github.com/user-attachments/assets/4ccd1216-1c32-4e38-90dc-072732720884)

Create users, that have access to the Pre-Processing App (using credentials: usernames and passwords).
![image](https://github.com/user-attachments/assets/5c1f80ab-96f2-40af-93c4-7c30014771c3)


### The Client secret in the keycloak Realm and the flask application should match in order for the appication to have access to keycloak services














