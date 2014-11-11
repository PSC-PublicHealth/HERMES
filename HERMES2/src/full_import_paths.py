#! /usr/bin/env python

########################################################################
#  Copyright C 2012, Pittsburgh Supercomputing Center (PSC).            #
# =========================================================            #
#                                                                      #
# Permission to use, copy, and modify this software and its            #
# documentation without fee for personal use or non-commercial use     #
# within your organization is hereby granted, provided that the above  #
# copyright notice is preserved in all copies and that the copyright   #
# and this permission notice appear in supporting documentation.       #
# Permission to redistribute this software to other organizations or   #
# individuals is not permitted without the written permission of the   #
# Pittsburgh Supercomputing Center.  PSC makes no representations      #
# about the suitability of this software for any purpose.  It is       #
# provided "as is" without express or implied warranty.                #
#                                                                      #
########################################################################

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
