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
from horizon import workflows

from openstack_dashboard.api import sahara as saharaclient
from openstack_dashboard.dashboards.project.data_processing \
    .utils import helpers

LOG = logging.getLogger(__name__)


class GeneralConfigAction(workflows.Action):
    data_source_name = forms.CharField(label=_("Name"))

    data_source_type = forms.ChoiceField(
        label=_("Data Source Type"),
        choices=[("swift", "Swift"), ("hdfs", "HDFS"), ("maprfs", "MapR FS")],
        widget=forms.Select(attrs={
            "class": "switchable",
            "data-slug": "ds_type"
        }))

    data_source_url = forms.CharField(label=_("URL"))

    data_source_credential_user = forms.CharField(
        label=_("Source username"),
        required=False,
        widget=forms.TextInput(attrs={
            "class": "switched",
            "data-switch-on": "ds_type",
            "data-ds_type-swift": _("Source username")
        }))

    data_source_credential_pass = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'switched',
            'data-switch-on': 'ds_type',
            'data-ds_type-swift': _("Source password"),
            'autocomplete': 'off'
        }),
        label=_("Source password"),
        required=False)

    data_source_description = forms.CharField(
        label=_("Description"),
        required=False,
        widget=forms.Textarea(attrs={'rows': 4}))

    def __init__(self, request, *args, **kwargs):
        super(GeneralConfigAction, self).__init__(request, *args, **kwargs)

    class Meta(object):
        name = _("Create Data Source")
        help_text_template = ("project/data_processing.data_sources/"
                              "_create_data_source_help.html")


class GeneralConfig(workflows.Step):
    action_class = GeneralConfigAction

    def contribute(self, data, context):
        for k, v in data.items():
            context["general_" + k] = v

        context["source_url"] = context["general_data_source_url"]

        if context["general_data_source_type"] == "swift":
            if not context["general_data_source_url"].startswith("swift://"):
                context["source_url"] = "swift://{0}".format(
                    context["general_data_source_url"])

        return context


class CreateDataSource(workflows.Workflow):
    slug = "create_data_source"
    name = _("Create Data Source")
    finalize_button_name = _("Create")
    success_message = _("Data source created")
    failure_message = _("Could not create data source")
    success_url = "horizon:project:data_processing.data_sources:index"
    default_steps = (GeneralConfig, )

    def handle(self, request, context):
        try:
            self.object = saharaclient.data_source_create(
                request,
                context["general_data_source_name"],
                context["general_data_source_description"],
                context["general_data_source_type"],
                context["source_url"],
                context.get("general_data_source_credential_user", None),
                context.get("general_data_source_credential_pass", None))

            hlps = helpers.Helpers(request)
            if hlps.is_from_guide():
                request.session["guide_datasource_id"] = self.object.id
                request.session["guide_datasource_name"] = self.object.name
                self.success_url = (
                    "horizon:project:data_processing.wizard:jobex_guide")
            return True
        except Exception:
            exceptions.handle(request)
            return False
