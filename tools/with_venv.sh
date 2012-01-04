#!/bin/bash
TOOLS=`dirname $0`
VENV=$TOOLS/../.horizon-venv
source $VENV/bin/activate && $@
