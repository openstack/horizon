# Copyright 2015, Thales Services SAS
# All Rights Reserved.
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

from horizon import tabs

from openstack_dashboard.api import neutron as api
from openstack_dashboard.dashboards.project.routers.extensions.extraroutes\
    import tables as ertbl


LOG = logging.getLogger(__name__)


class ExtraRoutesTab(tabs.TableTab):
    table_classes = (ertbl.ExtraRoutesTable,)
    name = _("Static Routes")
    slug = "extraroutes"
    template_name = "horizon/common/_detail_table.html"

    def allowed(self, request):
        try:
            return api.is_extension_supported(request, 'extraroute')
        except Exception as e:
            LOG.info("Failed to check if Neutron extraroute extension is "
                     "supported: %s", e)
            return False

    def get_extra_routes_data(self):
        try:
            extraroutes = getattr(self.tab_group.kwargs['router'], 'routes')
        except AttributeError:
            extraroutes = []
        return [api.RouterStaticRoute(r) for r in extraroutes]
