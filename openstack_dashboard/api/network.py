# Copyright 2013 NEC Corporation
#
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

"""Abstraction layer for networking functionalities.

Currently Nova and Neutron have duplicated features. This API layer is
introduced to abstract the differences between them for seamless consumption by
different dashboard implementations.
"""

from openstack_dashboard.api import base
from openstack_dashboard.api import neutron


def servers_update_addresses(request, servers, all_tenants=False):
    """Retrieve servers networking information from Neutron if enabled.

       Should be used when up to date networking information is required,
       and Nova's networking info caching mechanism is not fast enough.

    """
    # NOTE(amotoki): This check is still needed because 'instances' panel
    # calls this method. We dropped security group and floating IP support
    # through Nova API (due to novaclient 8.0.0 drops their supports),
    # but we can still support 'Instances' panel with nova-network.
    # TODO(amotoki): Nova networkinfo info caching mechanism is now fast enough
    # as they are updated by Neutron via Nova event callback mechasm,
    # so servers_update_addresses is no longer needed.
    # We can reduce API calls by dropping it.
    neutron_enabled = base.is_service_enabled(request, 'network')
    if neutron_enabled:
        neutron.servers_update_addresses(request, servers, all_tenants)
