#!/bin/bash

# This script will be executed inside post_test_hook function in devstack gate

set -x

# install avconv to capture video of failed tests
sudo apt-get install -y libav-tools && export AVCONV_INSTALLED=1

sudo wget -q -O firefox.deb https://sourceforge.net/projects/ubuntuzilla/files/mozilla/apt/pool/main/f/firefox-mozilla-build/firefox-mozilla-build_46.0.1-0ubuntu1_amd64.deb/download
sudo apt-get -y purge firefox
sudo dpkg -i firefox.deb
sudo rm firefox.deb

HORIZON_DIR=/opt/stack/new/horizon
pushd $HORIZON_DIR
sudo -H -E -u stack tox -e py27integration
retval=$?

if [ -d openstack_dashboard/test/integration_tests/test_reports/ ]; then
  popd
  cp -r $HORIZON_DIR/openstack_dashboard/test/integration_tests/test_reports/ ./
fi
exit $retval
