#!/bin/bash
TOOLS=`dirname $0`
VENV=$TOOLS/../.dashboard-venv
source $VENV/bin/activate && $@

