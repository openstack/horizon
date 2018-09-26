# Copyright 2017 Rackspace, Inc.
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

from openstack_dashboard import api

import horizon


class Backups(horizon.Panel):
    name = _("Backups")
    slug = 'backups'
    permissions = (
        ('openstack.services.volume', 'openstack.services.volumev2',
         'openstack.services.volumev3'),
    )
    policy_rules = (("volume", "backup:get_all"),)

    @staticmethod
    def can_register():
        return api.cinder.volume_backup_supported(None)
