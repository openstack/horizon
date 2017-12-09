# Copyright 2014, Rackspace, US, Inc.
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
"""This package holds the REST API that supports the Horizon dashboard
Javascript code.

It is not intended to be used outside of Horizon, and makes no promises of
stability or fitness for purpose outside of that scope.

It does not promise to adhere to the general OpenStack API Guidelines set out
in https://wiki.openstack.org/wiki/APIChangeGuidelines.
"""

from openstack_dashboard.api.rest import cinder
from openstack_dashboard.api.rest import config
from openstack_dashboard.api.rest import glance
from openstack_dashboard.api.rest import keystone
from openstack_dashboard.api.rest import network
from openstack_dashboard.api.rest import neutron
from openstack_dashboard.api.rest import nova
from openstack_dashboard.api.rest import policy
from openstack_dashboard.api.rest import swift


__all__ = [
    'cinder',
    'config',
    'glance',
    'keystone',
    'network',
    'neutron',
    'nova',
    'policy',
    'swift',
]
