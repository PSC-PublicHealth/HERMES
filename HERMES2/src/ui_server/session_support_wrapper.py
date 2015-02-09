#!/usr/bin/env python

###################################################################################
# Copyright © 2015, Pittsburgh Supercomputing Center (PSC).  All Rights Reserved. #
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

################
# To use beaker instead of storing the session in HERMES' own SQLALCHEMY, swap the
# commenting on the following lines
#
#import session_support_beaker # Needed to trigger SQLAlchemy @UnusedImport
#from session_support_beaker import * # This actually makes the namespace available for import
import session_support # Needed to trigger SQLAlchemy @UnusedImport
from session_support import * # This actually makes the namespace available for import
#############

