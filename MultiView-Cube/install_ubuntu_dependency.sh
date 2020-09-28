#!/bin/bash

PY_VER_ARR=($(python3 --version | awk '{print $2}' | tr "." "\n"))
PY_MAJOR_VER=${PY_VER_ARR[0]}
PY_MINOR_VER=${PY_VER_ARR[1]}
PY_SUB_VER=${PY_VER_ARR[2]}

if (( ${PY_MAJOR_VER} != 3 || ${PY_MINOR_VER} < 6))
then
    sudo add-apt-repository -y ppa:deadsnakes/ppa
    sudo apt update
    sudo apt install -y python3.6 python3.6-dev python3-pip build-essential libssl-dev libffi-dev libxml2-dev libxslt1-dev zlib1g-dev 
    sudo apt-get install -y libvirt-dev screen


    sudo update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.6 1
fi

sudo python3 -m pip install -r ./requirements.txt