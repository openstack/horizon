#!/bin/bash

# This script will be executed inside post_test_hook function in devstack gate

set -x

cd /opt/stack/new/horizon
sudo -H -u stack tox -e py27integration
retval=$?

if [ -d openstack_dashboard/test/integration_tests/test_reports/ ]; then
  cp -r openstack_dashboard/test/integration_tests/test_reports/ /home/jenkins/workspace/gate-horizon-dsvm-integration/
fi
exit $retval

