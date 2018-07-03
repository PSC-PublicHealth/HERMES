#!/usr/bin/env python


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

