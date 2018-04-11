# Copyright 2017 Ericsson
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

import logging

from django.utils.translation import ugettext_lazy as _

import horizon

from openstack_dashboard.api import neutron

LOG = logging.getLogger(__name__)


class Trunks(horizon.Panel):
    name = _("Trunks")
    slug = "trunks"
    permissions = ('openstack.services.network',)
    policy_rules = (("trunk", "context_is_admin"),)

    def allowed(self, context):
        request = context['request']
        try:
            return (
                super(Trunks, self).allowed(context) and
                request.user.has_perms(self.permissions) and
                neutron.is_extension_supported(request,
                                               extension_alias='trunk')
            )
        except Exception:
            LOG.error("Call to list enabled services failed. This is likely "
                      "due to a problem communicating with the Neutron "
                      "endpoint. Trunks admin panel will not be displayed.")
            return False
