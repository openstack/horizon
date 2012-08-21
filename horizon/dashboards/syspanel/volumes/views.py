# vim: tabstop=4 shiftwidth=4 softtabstop=4

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

"""
Admin views for managing Nova volumes.
"""

from horizon.dashboards.nova.volumes.views import (IndexView as _IndexView,
                                                   DetailView as _DetailView)
from .tables import VolumesTable


class IndexView(_IndexView):
    table_class = VolumesTable
    template_name = "syspanel/volumes/index.html"

    def get_data(self):
        volumes = self._get_volumes(search_opts={'all_tenants': 1})
        instances = self._get_instances()
        self._set_id_if_nameless(volumes, instances)
        self._set_attachments_string(volumes, instances)
        return volumes


class DetailView(_DetailView):
    template_name = "syspanel/volumes/detail.html"
