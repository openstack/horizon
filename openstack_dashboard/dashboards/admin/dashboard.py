# Copyright 2012 Nebula, Inc.
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
from openstack_auth import utils

import horizon
from horizon.utils import settings as utils_settings


class Admin(horizon.Dashboard):
    name = _("Admin")
    slug = "admin"

    if utils_settings.import_setting("POLICY_CHECK_FUNCTION"):
        policy_rules = (('identity', 'admin_required'),
                        ('image', 'context_is_admin'),
                        ('volume', 'context_is_admin'),
                        ('compute', 'context_is_admin'),
                        ('network', 'context_is_admin'),)
    else:
        permissions = (tuple(utils.get_admin_permissions()),)


horizon.register(Admin)
