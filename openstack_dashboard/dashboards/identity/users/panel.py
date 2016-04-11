# Copyright 2012 United States Government as represented by the
# Administrator of the National Aeronautics and Space Administration.
# All Rights Reserved.
#
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

import horizon

from openstack_dashboard.api import keystone


class Users(horizon.Panel):
    name = _("Users")
    slug = 'users'
    policy_rules = (("identity", "identity:get_user"),
                    ("identity", "identity:list_users"))

    def can_access(self, context):
        if keystone.is_multi_domain_enabled() \
                and not keystone.is_domain_admin(context['request']):
            return False
        return super(Users, self).can_access(context)
