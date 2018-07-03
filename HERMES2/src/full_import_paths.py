#! /usr/bin/env python


_hermes_svn_id_="$Id$"

import sys, os, os.path

cwd = os.path.dirname(__file__)

if cwd not in sys.path:
    try:
        sys.path.append(cwd)
    except:
        pass

paths = ['sim',
         'sim/db',
         'sim/hermes_types',
         'sim/models',
         'sim/route_types',
         'utils',
         'tools',
         'tools/visualization',
         'ui_server',
         'ui_server/thirdparty/bottle-0.11.6',
         'ui_server/thirdparty/bottle_sqlalchemy',
         'ui_server/thirdparty/SimPy/simpy-2.3.1'
         ]

try:
    fullpaths = [os.path.join(cwd, path) for path in paths]
    fullpaths = [p for p in fullpaths if p not in sys.path]
    sys.path = fullpaths + sys.path
except:
    pass

HermesBaseDir = os.path.normpath(os.path.join(cwd, '..'))
print HermesBaseDir
