#!/bin/bash
# this already exists inside template.app as Contents/Resources/script
cd $( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )
cd HERMES2
export LANG="en_US.UTF-8"
export LC_COLLATE="en_US.UTF-8"
export LC_CTYPE="en_US.UTF-8"
export LC_MESSAGES="en_US.UTF-8"
export LC_MONETARY="en_US.UTF-8"
export LC_NUMERIC="en_US.UTF-8"
export LC_TIME="en_US.UTF-8"
python src/tools/thirdparty/virtualenv/virtualenv.py python
source python/bin/activate
pip install --upgrade pip
#	echo Current dir:
#	pwd
#	echo Test virtualenv:
#	python envtest.py
python src/tools/install_hermes.py
#../browse.sh&
cd src/tools
python hermes_ui.py
#python -v
#pip freeze
#cd ../..
#../browse.sh