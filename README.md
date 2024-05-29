# Setup and Run Guide for Your Application

This guide provides detailed instructions on how to set up and run the application on an Ubuntu 20+ .

## Prerequisites
Before starting, ensure that you have the following software installed on your System:

1. Docker
2. Docker Compose
3. Git

If these are not installed, follow the steps below to install them.

## ## ## Step 1: Install Docker
Update the package database:
==================================
sudo apt update

Install prerequisite packages:
==================================
sudo apt install apt-transport-https ca-certificates curl software-properties-common -y

Add Docker’s official GPG key:
==================================
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo apt-key add -

Add Docker repository:
==================================
sudo add-apt-repository "deb [arch=amd64] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable"


Install Docker:
==================================
sudo apt update
sudo apt install docker-ce -y


Start Docker and enable it to start on boot:
==================================
sudo systemctl start docker
sudo systemctl enable docker

## Step 2: Install Docker Compose
Download the Docker Compose binary:
==================================
sudo curl -L "https://github.com/docker/compose/releases/download/1.29.2/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose

Apply executable permissions to the binary:
==================================
sudo chmod +x /usr/local/bin/docker-compose

Verify the installation:
==================================
docker-compose --version


## Step 3: Install Git
Update the package database (if not already done):
==================================
sudo apt update

Install Git:
==================================
sudo apt install git -y


## Step 4: Clone the Repository
Navigate to the directory where you want to clone the repository:
==================================
cd /path/to/your/desired/folder

Clone your repository:
==================================
git clone https://github.com/yourusername/yourrepository.git

Navigate into the cloned repository:
==================================
cd yourrepository


## Step 5: Set Up and Run the Application
Run the docker-compose-services.yml file to set up the necessary services:
==================================
docker-compose -f docker-compose-services.yml up -d

Run the docker-compose.yml file to start the basic Flask application:
==================================
docker-compose up -d


## Step 6: Verify the Setup
Check if all the containers are running:
==================================
docker ps

Access your application by navigating to the appropriate URL in your web browser. If your Flask application is running on port 5000, you can typically access it at:
==================================
http://<your-vm-ip>:5000

Additional Tips
To stop the containers, use:
==================================
docker-compose down

To view the logs of a specific container, use:
==================================
docker logs <container_id>