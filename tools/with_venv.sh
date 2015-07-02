#!/bin/bash
TOOLS_PATH=${TOOLS_PATH:-$(dirname $0)}
VENV_PATH=${VENV_PATH:-${TOOLS_PATH}}
VENV_DIR=${VENV_NAME:-/../.venv}
TOOLS=${TOOLS_PATH}
VENV=${VENV:-${VENV_PATH}/${VENV_DIR}}
HORIZON_DIR=${TOOLS%/tools}

# This horrible mangling of the PYTHONPATH is required to get the
# babel-angular-gettext extractor to work. To fix this the extractor needs to
# be packaged on pypi and added to global requirements. That work is in progress.
export PYTHONPATH="$HORIZON_DIR"
source ${VENV}/bin/activate && "$@"
