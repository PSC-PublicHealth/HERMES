#! /usr/bin/env python


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
