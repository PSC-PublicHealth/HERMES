#!/bin/bash
# Everything is relative to the HERMES2 top-level directory.
# Assume that this script is in HERMES2/src

THISDIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

THISDIR=`dirname $THISDIR`

export HERMES_BASE=$THISDIR

HERMES_DATA_PATH=""

for d in $HERMES_BASE/master_data/*; do echo `basename $d` / `basename $d/*.kvp`; HERMES_DATA_PATH=$d:$HERMES_DATA_PATH; done;

export HERMES_DATA_PATH

alias hermes=$HERMES_BASE/src/sim/main.py

