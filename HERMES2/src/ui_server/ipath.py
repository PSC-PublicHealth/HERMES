#! /usr/bin/env python

########################################################################
# Copyright C 2012, Pittsburgh Supercomputing Center (PSC).            #
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
