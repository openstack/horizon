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
from horizon import forms

from openstack_dashboard.api import sahara as saharaclient
from openstack_dashboard.dashboards.project.data_processing. \
    utils import workflow_helpers

LOG = logging.getLogger(__name__)


class UploadFileForm(forms.SelfHandlingForm,
                     workflow_helpers.PluginAndVersionMixin):
    template_name = forms.CharField(max_length=80,
                                    label=_("Cluster Template Name"))

    def __init__(self, request, *args, **kwargs):
        super(UploadFileForm, self).__init__(request, *args, **kwargs)

        sahara = saharaclient.client(request)
        self._generate_plugin_version_fields(sahara)

        self.fields['template_file'] = forms.FileField(label=_("Template"))

    def handle(self, request, data):
        try:
            # we can set a limit on file size, but should we?
            filecontent = self.files['template_file'].read()

            plugin_name = data['plugin_name']
            hadoop_version = data.get(plugin_name + "_version")

            saharaclient.plugin_convert_to_template(request,
                                                    plugin_name,
                                                    hadoop_version,
                                                    data['template_name'],
                                                    filecontent)
            return True
        except Exception:
            exceptions.handle(request,
                              _("Unable to upload cluster template file"))
            return False
