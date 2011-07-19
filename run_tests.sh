#!/bin/bash

cd django-openstack
python bootstrap.py
bin/buildout
bin/test
# get results of the django-openstack tests
OPENSTACK_RESULT=$?

cd ../openstack-dashboard
python tools/install_venv.py

cp local/local_settings.py.example local/local_settings.py
tools/with_venv.sh dashboard/manage.py test
# get results of the openstack-dashboard tests
DASHBOARD_RESULT=$?

exit $(($OPENSTACK_RESULT || $DASHBOARD_RESULT))
