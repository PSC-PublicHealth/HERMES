#! /usr/bin/env python


__doc__=""" This wipes the whole db
"""
_hermes_svn_id_="$Id$"

import os.path
import sys
import db_routines

try:
    cwd = os.path.dirname(__file__)
    if cwd not in sys.path:
        sys.path.append(cwd)

    # also need the directory above
    updir = os.path.join(cwd, '..')
    if updir not in sys.path:
        sys.path.append(updir)
except:
    pass

def main():
    import ipath
    import shadow_network
    import session_support_wrapper as session_support
    iface = db_routines.DbInterface(echo=True)
    iface.dropTables(IReallyWantToDoThis=True)

############
# Main hook
############

if __name__=="__main__":
    main()

