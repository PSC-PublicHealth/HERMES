#!/bin/bash
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
# Everything is relative to the HERMES2 top-level directory.
# Assume that this script is in HERMES2/src

THISDIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

THISDIR=`dirname $THISDIR`

export HERMES_BASE=$THISDIR

HERMES_DATA_PATH=""

for d in $HERMES_BASE/master_data/*; do echo `basename $d` / `basename $d/*.kvp`; HERMES_DATA_PATH=$d:$HERMES_DATA_PATH; done;

export HERMES_DATA_PATH

alias hermes=$HERMES_BASE/src/sim/main.py

