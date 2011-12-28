# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright 2011 Nebula, Inc.
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

from django.utils.translation import ugettext as _

import horizon


class Nova(horizon.Dashboard):
    name = "Project"
    slug = "nova"
    panels = {_("Manage Compute"): ('overview',
                                    'instances_and_volumes',
                                    'access_and_security',
                                    'images_and_snapshots'),
              _("Network"): ('networks',),
              _("Object Store"): ('containers',)}
    default_panel = 'overview'
    supports_tenants = True


horizon.register(Nova)
