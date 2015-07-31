# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
# implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import logging

from django.utils.translation import ugettext_lazy as _
from saharaclient.api import base as api_base

from horizon import exceptions
from horizon import forms

from openstack_dashboard.contrib.sahara.api import sahara as saharaclient

import openstack_dashboard.contrib.sahara.content.data_processing. \
    nodegroup_templates.workflows.create as create_flow
import openstack_dashboard.contrib.sahara.content.data_processing. \
    nodegroup_templates.workflows.copy as copy_flow
from openstack_dashboard.contrib.sahara.content.data_processing.utils \
    import workflow_helpers

LOG = logging.getLogger(__name__)


class EditNodegroupTemplate(copy_flow.CopyNodegroupTemplate):
    success_message = _("Node Group Template %s updated")
    finalize_button_name = _("Update")
    name = _("Edit Node Group Template")

    def __init__(self, request, context_seed, entry_point, *args, **kwargs):
        super(EditNodegroupTemplate, self).__init__(request, context_seed,
                                                    entry_point, *args,
                                                    **kwargs)

        for step in self.steps:
            if not isinstance(step, create_flow.GeneralConfig):
                continue
            fields = step.action.fields
            fields["nodegroup_name"].initial = self.template.name

        fields["template_id"] = forms.CharField(
            widget=forms.HiddenInput(),
            initial=self.template_id
        )

    def handle(self, request, context):
        try:
            processes = []
            for service_process in context["general_processes"]:
                processes.append(str(service_process).split(":")[1])

            configs_dict = (
                workflow_helpers.parse_configs_from_context(
                    context, self.defaults))

            plugin, hadoop_version = (
                workflow_helpers.get_plugin_and_hadoop_version(request))

            volumes_per_node = None
            volumes_size = None
            volumes_availability_zone = None
            volume_type = None
            volume_local_to_instance = False

            if context["general_storage"] == "cinder_volume":
                volumes_per_node = context["general_volumes_per_node"]
                volumes_size = context["general_volumes_size"]
                volume_type = context["general_volume_type"]
                volume_local_to_instance = \
                    context["general_volume_local_to_instance"]
                volumes_availability_zone = \
                    context["general_volumes_availability_zone"]

            saharaclient.nodegroup_template_update(
                request=request,
                ngt_id=self.template_id,
                name=context["general_nodegroup_name"],
                plugin_name=plugin,
                hadoop_version=hadoop_version,
                flavor_id=context["general_flavor"],
                description=context["general_description"],
                volumes_per_node=volumes_per_node,
                volumes_size=volumes_size,
                volume_type=volume_type,
                volume_local_to_instance=volume_local_to_instance,
                volumes_availability_zone=volumes_availability_zone,
                node_processes=processes,
                node_configs=configs_dict,
                floating_ip_pool=context.get("general_floating_ip_pool"),
                security_groups=context["security_groups"],
                auto_security_group=context["security_autogroup"],
                availability_zone=context["general_availability_zone"],
                use_autoconfig=context['general_use_autoconfig'],
                is_proxy_gateway=context["general_proxygateway"])
            return True
        except api_base.APIException as e:
            self.error_description = str(e.message)
            return False
        except Exception:
            exceptions.handle(request)
