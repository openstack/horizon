#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

# The slug of the dashboard to be added to HORIZON['dashboards']. Required.
DASHBOARD = 'identity'
# If set to True, this dashboard will be set as the default dashboard.
DEFAULT = False
# A dictionary of exception classes to be added to HORIZON['exceptions'].
ADD_EXCEPTIONS = {}
# A list of applications to be added to INSTALLED_APPS.
ADD_INSTALLED_APPS = ['openstack_dashboard.dashboards.identity']

ADD_ANGULAR_MODULES = [
    'hz.dashboard',
    'hz.dashboard.identity',
]

ADD_JS_FILES = [
    'dashboard/identity/identity.module.js',
    'dashboard/identity/users/users.module.js',
]

ADD_JS_SPEC_FILES = [
    'dashboard/identity/identity.module.spec.js',
    'dashboard/identity/users/users.module.spec.js',
]

ADD_SCSS_FILES = [
    'dashboard/identity/identity.scss'
]
