#! /usr/bin/env python


_hermes_svn_id_="$Id: ipath.py 1301 2013-05-15 19:07:16Z jleonard $"

import sys, os, os.path
cwd = os.path.dirname(__file__)

newdir = os.path.join(cwd, '../..')
if newdir not in sys.path:
    sys.path.append(newdir)

import full_import_paths
