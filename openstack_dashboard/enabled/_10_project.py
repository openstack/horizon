# Copyright 2015, Hewlett-Packard Development Company, L.P.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# The slug of the dashboard to be added to HORIZON['dashboards']. Required.
DASHBOARD = 'project'
# If set to True, this dashboard will be set as the default dashboard.
DEFAULT = True
# A dictionary of exception classes to be added to HORIZON['exceptions'].
ADD_EXCEPTIONS = {}
# A list of applications to be added to INSTALLED_APPS.
ADD_INSTALLED_APPS = ['openstack_dashboard.dashboards.project']

ADD_ANGULAR_MODULES = ['hz.dashboard']

LAUNCH_INST = 'dashboard/launch-instance/'

ADD_JS_FILES = [
    'dashboard/dashboard.module.js',
    'dashboard/workflow/workflow.js',
    'dashboard/cloud-services/cloud-services.js',
    LAUNCH_INST + 'launch-instance.js',
    LAUNCH_INST + 'launch-instance.model.js',
    LAUNCH_INST + 'source/source.js',
    LAUNCH_INST + 'flavor/flavor.js',
    LAUNCH_INST + 'flavor/select-flavor-table.js',
    LAUNCH_INST + 'network/network.js',
    LAUNCH_INST + 'security-groups/security-groups.js',
    LAUNCH_INST + 'keypair/keypair.js',
    LAUNCH_INST + 'configuration/configuration.js',
    LAUNCH_INST + 'configuration/load-edit.js',
]

ADD_JS_SPEC_FILES = [
    'dashboard/dashboard.module.spec.js',
    'dashboard/workflow/workflow.spec.js',
    'dashboard/cloud-services/cloud-services.spec.js',
    LAUNCH_INST + 'launch-instance.spec.js',
    LAUNCH_INST + 'launch-instance.model.spec.js',
    LAUNCH_INST + 'source/source.spec.js',
    LAUNCH_INST + 'flavor/flavor.spec.js',
    LAUNCH_INST + 'network/network.spec.js',
    LAUNCH_INST + 'security-groups/security-groups.spec.js',
    LAUNCH_INST + 'keypair/keypair.spec.js',
    LAUNCH_INST + 'configuration/configuration.spec.js',
]
