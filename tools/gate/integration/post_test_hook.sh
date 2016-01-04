#!/bin/bash

# This script will be executed inside post_test_hook function in devstack gate

cd /opt/stack/new/horizon
sudo -H -u stack tox -e py27integration
retval=$?
if [ -d openstack_dashboard/test/integration_tests/integration_tests_screenshots/ ]; then
  cp -r openstack_dashboard/test/integration_tests/integration_tests_screenshots/ /home/jenkins/workspace/gate-horizon-dsvm-integration/
fi
exit $retval

