#!/bin/bash
cd $( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )

cd HERMES2

export LANG="en_US.UTF-8"
export LC_COLLATE="en_US.UTF-8"
export LC_CTYPE="en_US.UTF-8"
export LC_MESSAGES="en_US.UTF-8"
export LC_MONETARY="en_US.UTF-8"
export LC_NUMERIC="en_US.UTF-8"
export LC_TIME="en_US.UTF-8"

#python src/tools/thirdparty/virtualenv/virtualenv.py python

export HERMES_VENV=`pwd`/python_environment

if [ ! -f .INSTALL_HERMES_COMPLETE ]; then
    curl -O https://files.pythonhosted.org/packages/b1/72/2d70c5a1de409ceb3a27ff2ec007ecdd5cc52239e7c74990e32af57affe9/virtualenv-15.2.0.tar.gz 
    tar xzvf virtualenv-15.2.0.tar.gz
    python virtualenv-15.2.0/virtualenv.py $HERMES_VENV
fi

source $HERMES_VENV/bin/activate

if [ ! -f .INSTALL_HERMES_COMPLETE ]; then

    pip install --upgrade pip
    pip install -U setuptools
    pip install -r requirements.txt

    #	echo Current dir:
    #	pwd
    #	echo Test virtualenv:
    #	python envtest.py
    python src/tools/install_hermes.py
    #../browse.sh&
    echo "Please start HERMES from Launchpad or from your Applications folder"
    touch .INSTALL_HERMES_COMPLETE
else
    cd src/tools
    python hermes_ui.py
fi

#python -v
#pip freeze
#cd ../..
#../browse.sh
