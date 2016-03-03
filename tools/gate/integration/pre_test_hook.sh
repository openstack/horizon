#!/bin/bash

# This script will be executed inside pre_test_hook function in devstack gate

cd /opt/stack/new/horizon/openstack_dashboard/local/local_settings.d
mv _20_integration_tests_scaffolds.py.example _20_integration_tests_scaffolds.py
sudo service apache2 restart
