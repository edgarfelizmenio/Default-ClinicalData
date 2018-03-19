#! /bin/bash -x

apt-get -y -q update
apt-get -y -q upgrade
apt-get -y -q install htop
apt-get -y -q install build-essential
apt-get -y -q install git
apt-get -y -q install vim

apt-get -y -q install python python dev
apt-get -y -q install python-pip

apt-get -y -q install libssl-dev libffi-dev python3-dev
apt-get -y -q install python3-pip
apt-get -y -q install python3.4-venv

apt-get -y -q install nginx

# change this
cd /home/MEDIATOR-CLINICAL-DATA

pyvenv-3.4 Default-ClinicalData/env
source Default-ClinicalData/env/bin/activate
pip3 install --upgrade pip

pip3 install -r Default-ClinicalData/requirements.txt

# install gunicorn
pip3 install gunicorn

# install and enable nginx
cp nginx/mediator-clinicaldata /etc/nginx/sites-available/mediator-clinicaldata
ln -s /etc/nginx/sites-available/mediator-clinicaldata /etc/nginx/sites-enabled/mediator-clinicaldata
sudo service nginx restart

# start the mediator
cp upstart/mediator-clinicaldata.conf /etc/init/mediator-clinicaldata.conf
sudo service mediator-clinicaldata start