#!/bin/bash

# This script will be executed inside pre_test_hook function in devstack gate

set -x

HORIZON_CODE_DIR=/opt/stack/new/horizon

cd ${HORIZON_CODE_DIR}/openstack_dashboard/local/local_settings.d
mv _20_integration_tests_scaffolds.py.example _20_integration_tests_scaffolds.py

if [ "$1" == "deprecated" ] ; then

mv _2010_integration_tests_deprecated.py.example _2010_integration_tests_deprecated.py
cat > ${HORIZON_CODE_DIR}/openstack_dashboard/test/integration_tests/local-horizon.conf <<EOF
[image]
panel_type=legacy

[flavors]
panel_type=legacy
EOF

fi
