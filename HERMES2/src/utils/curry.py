#!/usr/bin/env python

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

__doc__=""" curry.py
For an explanation of this, look up 'currying' and 'currying in python'
"""
_hermes_svn_id_="$Id$"

import types

##############
# Notes-
# -my 'curry' is doing the case where len(args)<=1 incorrectly?
##############

# For an explanation of this, look up 'currying' and 'currying in python'
def curry(*args, **kwargs):
    """
    For an explanation of this, look up 'currying' and 'currying in python'
    """
    function, args = args[0], args[1:]
    #print "curry: args %s"%str(args)
    if args and kwargs:
        def result(*rest, **kwrest):
            combined = kwargs.copy()
            combined.update(kwrest)
            return function(*args + rest, **combined)
    elif args:
        if len(args) > 1 or args[0] is None:
            def result(*rest, **kwrest):
                return function(*args + rest, **kwrest)
        else:
            def result(*rest, **kwrest):
                return function(*args+rest, **kwrest)
            # Special magic: make a bound object method on the arg
            #return new.instancemethod(function, args[0], object)
            #return types.MethodType(function, args[0], object)
            
    elif kwargs:
        def result(*rest, **kwrest):
            if kwrest:
                combined = kwargs.copy()
                combined.update(kwrest)
            else:
                combined = kwargs
            return function(*rest, **combined)
    else:
        return function
    result.__doc__ = "Curried function '%s':\n%s" %\
        (function.func_name, function.func_doc)
    return result

