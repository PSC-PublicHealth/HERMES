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

