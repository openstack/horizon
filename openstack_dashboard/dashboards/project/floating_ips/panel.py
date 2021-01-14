# Copyright 2017 Cisco Systems, Inc.
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

from django.utils.translation import ugettext_lazy as _

import horizon

from openstack_dashboard.utils import settings as setting_utils


class FloatingIps(horizon.Panel):
    name = _("Floating IPs")
    slug = 'floating_ips'
    permissions = ('openstack.services.network',)

    @staticmethod
    def can_register():
        return setting_utils.get_dict_config(
            'OPENSTACK_NEUTRON_NETWORK', 'enable_router')
