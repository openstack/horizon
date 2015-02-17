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

from openstack_dashboard.api import sahara as saharaclient

import openstack_dashboard.dashboards.project.data_processing. \
    nodegroup_templates.workflows.create as create_flow

LOG = logging.getLogger(__name__)


class CopyNodegroupTemplate(create_flow.ConfigureNodegroupTemplate):
    success_message = _("Node Group Template copy %s created")

    def __init__(self, request, context_seed, entry_point, *args, **kwargs):
        template_id = context_seed["template_id"]
        template = saharaclient.nodegroup_template_get(request, template_id)
        self._set_configs_to_copy(template.node_configs)

        plugin = template.plugin_name
        hadoop_version = template.hadoop_version

        request.GET = request.GET.copy()
        request.GET.update(
            {"plugin_name": plugin, "hadoop_version": hadoop_version})

        super(CopyNodegroupTemplate, self).__init__(request, context_seed,
                                                    entry_point, *args,
                                                    **kwargs)

        g_fields = None
        s_fields = None
        for step in self.steps:
            if isinstance(step, create_flow.GeneralConfig):
                g_fields = step.action.fields
            if isinstance(step, create_flow.SecurityConfig):
                s_fields = step.action.fields

        g_fields["nodegroup_name"].initial = template.name + "-copy"
        g_fields["description"].initial = template.description
        g_fields["flavor"].initial = template.flavor_id

        if hasattr(template, "availability_zone"):
            g_fields["availability_zone"].initial = template.availability_zone

        if hasattr(template, "volumes_availability_zone"):
            g_fields["volumes_availability_zone"].initial = \
                template.volumes_availability_zone

        storage = "cinder_volume" if template.volumes_per_node > 0 \
            else "ephemeral_drive"
        volumes_per_node = template.volumes_per_node
        volumes_size = template.volumes_size
        g_fields["storage"].initial = storage
        g_fields["volumes_per_node"].initial = volumes_per_node
        g_fields["volumes_size"].initial = volumes_size

        if template.floating_ip_pool:
            g_fields['floating_ip_pool'].initial = template.floating_ip_pool

        s_fields["security_autogroup"].initial = template.auto_security_group

        if template.security_groups:
            s_fields["security_groups"].initial = dict(
                [(sg, sg) for sg in template.security_groups])

        processes_dict = dict()
        try:
            plugin_details = saharaclient.plugin_get_version_details(
                request,
                plugin,
                hadoop_version)
            plugin_node_processes = plugin_details.node_processes
        except Exception:
            plugin_node_processes = dict()
            exceptions.handle(request,
                              _("Unable to fetch plugin details."))
        for process in template.node_processes:
            # need to know the service
            _service = None
            for service, processes in plugin_node_processes.items():
                if process in processes:
                    _service = service
                    break
            processes_dict["%s:%s" % (_service, process)] = process
        g_fields["processes"].initial = processes_dict
