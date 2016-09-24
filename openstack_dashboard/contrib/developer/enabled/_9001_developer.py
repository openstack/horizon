# Copyright 2015 Cisco Systems, Inc.
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

DASHBOARD = 'developer'

ADD_ANGULAR_MODULES = [
    'horizon.dashboard.developer'
]

ADD_INSTALLED_APPS = [
    'openstack_dashboard.contrib.developer'
]

ADD_SCSS_FILES = [
    'dashboard/developer/developer.scss',
]

AUTO_DISCOVER_STATIC_FILES = True
