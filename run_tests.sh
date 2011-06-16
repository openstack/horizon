#!/bin/bash

cd django-openstack
python bootstrap.py
bin/buildout
bin/test

OPENSTACK_RESULT=$?

cd ../openstack-dashboard
python tools/install_venv.py

cp local/local_settings.py.example local/local_settings.py
tools/with_venv.sh dashboard/manage.py test

DASHBOARD_RESULT=$?

exit $(($OPENSTACK_RESULT || $DASHBOARD_RESULT))
