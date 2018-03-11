#!/bin/bash

if [[ $UID != 0 ]]; then
    echo "Please run this script with sudo:"
    echo "sudo $0 $*"
    exit 1
fi

deps="
configobj
configparser
fake_useragent
user_agents
openpyxl
selenium
urllib3
Flask-MySQLDb
tqdm
pycountry
cfscrape
"

install_python_dependencies() 
{
    for dep in $deps
    do
        pip3 install $dep
    done
}

install_linux_dependencies()
{
    apt-get install python3
    apt-get install python3-pip
    apt-get install libmysqlclient-dev
}

install_linux_dependencies
install_python_dependencies

