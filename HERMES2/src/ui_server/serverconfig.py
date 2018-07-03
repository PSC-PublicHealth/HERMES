#! /usr/bin/env python


__doc__ = """serverconfig
The module exists to provide server configuration parameters in a way which
avoids circular import problems.
"""

_hermes_svn_id_="$Id$"

rootPath = '/bottle_hermes/'

topPath = 'top' # so the generic entry URI looks like http://...hostandport.../bottle_hermes/top
topName = 'HERMES' 
