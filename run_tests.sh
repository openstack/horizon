#!/bin/bash

bzr branch lp:django-nova
python tools/install_venv.py django-nova

cp local/local_settings.py.example local/local_settings.py
tools/with_venv.sh dashboard/manage.py  test
