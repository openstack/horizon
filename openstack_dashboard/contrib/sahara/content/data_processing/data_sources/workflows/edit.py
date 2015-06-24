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

from openstack_dashboard.contrib.sahara.api import sahara as saharaclient
from openstack_dashboard.contrib.sahara.content.data_processing \
    .data_sources.workflows import create

LOG = logging.getLogger(__name__)


class EditDataSource(create.CreateDataSource):
    slug = "edit_data_source"
    name = _("Edit Data Source")
    finalize_button_name = _("Update")
    success_message = _("Data source updated")
    failure_message = _("Could not update data source")
    success_url = "horizon:project:data_processing.data_sources:index"
    default_steps = (create.GeneralConfig,)

    FIELD_MAP = {
        "data_source_name": "name",
        "data_source_type": "type",
        "data_source_description": "description",
        "data_source_url": "url",
        "data_source_credential_user": None,
        "data_source_credential_pass": None,
    }

    def __init__(self, request, context_seed, entry_point, *args, **kwargs):
        self.data_source_id = context_seed["data_source_id"]
        data_source = saharaclient.data_source_get(request,
                                                   self.data_source_id)
        super(EditDataSource, self).__init__(request, context_seed,
                                             entry_point, *args, **kwargs)
        for step in self.steps:
            if isinstance(step, create.GeneralConfig):
                fields = step.action.fields
                for field in fields:
                    if self.FIELD_MAP[field]:
                        fields[field].initial = getattr(data_source,
                                                        self.FIELD_MAP[field],
                                                        None)

    def handle(self, request, context):
        try:
            update_data = {
                "name": context["general_data_source_name"],
                "description": context["general_data_source_description"],
                "type": context["general_data_source_type"],
                "url": context["source_url"],
                "credentials": {
                    "user": context.get("general_data_source_credential_user",
                                        None),
                    "pass": context.get("general_data_source_credential_pass",
                                        None)
                }
            }
            return saharaclient.data_source_update(request,
                                                   self.data_source_id,
                                                   update_data)
        except Exception:
            exceptions.handle(request)
            return False
