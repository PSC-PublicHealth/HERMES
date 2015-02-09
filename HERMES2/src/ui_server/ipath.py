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

import sys, os.path
cwd = os.path.dirname(__file__)

candidatePaths = ['..']
existingDirs = []
for c in candidatePaths:
    newdir = os.path.join(cwd, c)
    if os.path.isdir(newdir): existingDirs.append(newdir)
    
if len(existingDirs) == 0:
    raise RuntimeError('ipath cannot find the main HERMES source directory')
elif len(existingDirs) > 1:
    raise RuntimeError('ipath found too many candidates to be the main HERMES directory')
else:
    if existingDirs[0] not in sys.path:
        sys.path.append(existingDirs[0])

import full_import_paths
