#!/bin/bash
TOOLS_PATH=${TOOLS_PATH:-$(dirname $0)}
VENV_PATH=${VENV_PATH:-${TOOLS_PATH}}
VENV_DIR=${VENV_NAME:-/../.venv}
TOOLS=${TOOLS_PATH}
VENV=${VENV:-${VENV_PATH}/${VENV_DIR}}
source ${VENV}/bin/activate && "$@"
