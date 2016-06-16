#!/bin/bash

# This script will be executed inside post_test_hook function in devstack gate

sudo wget -q -O firefox.deb https://sourceforge.net/projects/ubuntuzilla/files/mozilla/apt/pool/main/f/firefox-mozilla-build/firefox-mozilla-build_46.0.1-0ubuntu1_amd64.deb/download
sudo apt-get -y purge firefox
sudo dpkg -i firefox.deb
sudo rm firefox.deb

cd /opt/stack/new/horizon
sudo -H -u stack tox -e py27integration
retval=$?
if [ -d openstack_dashboard/test/integration_tests/integration_tests_screenshots/ ]; then
  cp -r openstack_dashboard/test/integration_tests/integration_tests_screenshots/ /home/jenkins/workspace/gate-horizon-dsvm-integration/
fi
exit $retval

