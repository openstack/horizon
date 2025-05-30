# Copyright 2013 Kylin, Inc.
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

from django.conf import settings
from django.utils.translation import gettext_lazy as _

import horizon


class Defaults(horizon.Panel):
    name = _("Default Quotas")
    slug = 'defaults'
    policy_rules = (("compute", "context_is_admin"),
                    ("volume", "context_is_admin"),)

    def allowed(self, context):
        if (('compute' in settings.SYSTEM_SCOPE_SERVICES) !=
                bool(context['request'].user.system_scoped)):
            return False
        return super().allowed(context)
