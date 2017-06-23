#! /usr/bin/env python

###################################################################################
# Copyright   2015, Pittsburgh Supercomputing Center (PSC).  All Rights Reserved. #
# =============================================================================== #
#                                                                                 #
# Permission to use, copy, and modify this software and its documentation without # 
# fee for personal use within your organization is hereby granted, provided that  #
# the above copyright notice is preserved in all copies and that the copyright    # 
# and this permission notice appear in supporting documentation.  All other       #
# restrictions and obligations are defined in the GNU Affero General Public       #
# License v3 (AGPL-3.0) located at http://www.gnu.org/licenses/agpl-3.0.html  A   #
# copy of the license is also provided in the top level of the source directory,  #
# in the file LICENSE.txt.                                                        #
#                                                                                 #
###################################################################################

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
