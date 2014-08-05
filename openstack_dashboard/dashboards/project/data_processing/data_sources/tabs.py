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


class GeneralTab(tabs.Tab):
    name = _("General Info")
    slug = "data_source_details_tab"
    template_name = ("project/data_processing.data_sources/_details.html")

    def get_context_data(self, request):
        data_source_id = self.tab_group.kwargs['data_source_id']
        try:
            data_source = saharaclient.data_source_get(request,
                                                       data_source_id)
        except Exception:
            exceptions.handle(self.tab_group.request,
                              _("Unable to retrieve data source details"))
            data_source = {}

        return {"data_source": data_source}


class DataSourceDetailsTabs(tabs.TabGroup):
    slug = "data_source_details"
    tabs = (GeneralTab,)
    sticky = True
