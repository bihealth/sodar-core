#!/usr/bin/env bash

echo "***********************************************"
echo "Installing Python 3.14"
echo "***********************************************"
add-apt-repository -y ppa:deadsnakes/ppa
apt-get -y update
apt-get -y install python3.14 python3.14-dev python3.14-venv python3.14-gdbm
curl https://bootstrap.pypa.io/get-pip.py | sudo -H python3.14
