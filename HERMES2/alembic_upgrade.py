#!/usr/bin/env python
import os.path, os
cwd = os.path.dirname(__file__)

addedPathStr = os.path.join(os.path.join(cwd, 'src'), 'sim')
addedPathStr += os.pathsep
addedPathStr = os.path.join(os.path.join(cwd, 'src'), 'ui_server')

try:
    path=os.environ['PYTHONPATH']
    path += os.pathsep
except:
    path=''

path += addedPathStr
os.environ['PYTHONPATH'] = path

os.system('alembic upgrade head')
