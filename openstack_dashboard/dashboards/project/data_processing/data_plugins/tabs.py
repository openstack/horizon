# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
# implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import logging

from django.utils.translation import ugettext_lazy as _

from horizon import exceptions
from horizon import tabs
from openstack_dashboard.api import sahara as saharaclient

LOG = logging.getLogger(__name__)


class DetailsTab(tabs.Tab):
    name = _("Details")
    slug = "plugin_details_tab"
    template_name = ("project/data_processing.data_plugins/_details.html")

    def get_context_data(self, request):
        plugin_id = self.tab_group.kwargs['plugin_id']
        plugin = None
        try:
            plugin = saharaclient.plugin_get(request, plugin_id)
        except Exception as e:
            LOG.error("Unable to get plugin with plugin_id %s (%s)" %
                      (plugin_id, str(e)))
            exceptions.handle(self.tab_group.request,
                              _('Unable to retrieve plugin.'))
        return {"plugin": plugin}


class PluginDetailsTabs(tabs.TabGroup):
    slug = "cluster_details"
    tabs = (DetailsTab,)
    sticky = True
