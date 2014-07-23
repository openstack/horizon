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
import openstack_dashboard.dashboards.project.data_processing. \
    utils.workflow_helpers as whelpers


LOG = logging.getLogger(__name__)


def anti_affinity_field():
    return forms.MultipleChoiceField(
        label=_("Use anti-affinity groups for: "),
        required=False,
        help_text=_("Use anti-affinity groups for processes"),
        widget=forms.CheckboxSelectMultiple()
    )


def populate_anti_affinity_choices(self, request, context):
    try:
        sahara = saharaclient.client(request)
        plugin, version = whelpers.get_plugin_and_hadoop_version(request)

        version_details = sahara.plugins.get_version_details(plugin, version)
        process_choices = []
        for processes in version_details.node_processes.values():
            for process in processes:
                process_choices.append((process, process))

        cluster_template_id = request.REQUEST.get("cluster_template_id", None)
        if cluster_template_id is None:
            selected_processes = request.REQUEST.get("aa_groups", [])
        else:
            cluster_template = (
                sahara.cluster_templates.get(cluster_template_id))
            selected_processes = cluster_template.anti_affinity

        checked_dict = dict()

        for process in selected_processes:
            checked_dict[process] = process

        self.fields['anti_affinity'].initial = checked_dict
    except Exception:
        process_choices = []
        exceptions.handle(request,
                          _("Unable to populate anti-affinity processes."))
    return process_choices
