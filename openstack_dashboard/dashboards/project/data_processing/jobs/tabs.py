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

from horizon import tabs

from openstack_dashboard.api import sahara as saharaclient

LOG = logging.getLogger(__name__)


class GeneralTab(tabs.Tab):
    name = _("General Info")
    slug = "job_details_tab"
    template_name = ("project/data_processing.jobs/_details.html")

    def get_context_data(self, request):
        job_id = self.tab_group.kwargs['job_id']
        job = saharaclient.job_get(request, job_id)
        return {"job": job}


class JobDetailsTabs(tabs.TabGroup):
    slug = "job_details"
    tabs = (GeneralTab,)
    sticky = True
