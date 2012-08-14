# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright 2012 Nebula, Inc.
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

import json
import logging

from django.utils.text import normalize_newlines
from django.utils.translation import ugettext_lazy as _
from django.utils.datastructures import SortedDict

from horizon import api
from horizon import exceptions
from horizon import messages

from horizon.dashboards.nova.instances import workflows as proj_workflows


LOG = logging.getLogger(__name__)


class AdminSetNetworkAction(proj_workflows.SetNetworkAction):

    class Meta:
        name = _("Networking")
        permissions = ('openstack.services.network',)
        help_text = _("Select networks for your instance.")

    def _get_tenant_list(self):
        if not hasattr(self, "_tenants"):
            try:
                tenants = api.keystone.tenant_list(self.request, admin=True)
            except:
                tenants = []
                msg = _('Unable to retrieve instance tenant information.')
                exceptions.handle(self.request, msg)

            tenant_dict = SortedDict([(t.id, t) for t in tenants])
            self._tenants = tenant_dict
        return self._tenants

    def populate_network_choices(self, request, context):
        try:
            networks = api.quantum.network_list(request)
            tenant_dict = self._get_tenant_list()
            network_list = []
            for network in networks:
                # To distinguish which network belonging to which tenant,
                # add tenant name as a prefix.
                network.set_id_as_name_if_empty()
                tenant_name = tenant_dict[network.tenant_id].name
                name = '%s:%s' % (tenant_name, network.name)
                # Encode as JSON to send network info as dict.
                key = json.dumps({'id': network.id,
                                  'name': network.name,
                                  'tenant_id': network.tenant_id})
                network_list.append((key, name))
        except:
            network_list = []
            exceptions.handle(request,
                              _('Unable to retrieve networks.'))
        return network_list


class AdminSetNetwork(proj_workflows.SetNetwork):
    action_class = AdminSetNetworkAction
    contributes = ("networks",)

    def contribute(self, data, context):
        if data:
            networks = self.workflow.request.POST.getlist("network")
            # If no networks are explicitly specified, network list
            # contains an empty string, so remove it.
            # In syspanel each element of networks is JSON-encoded dict.
            networks = [json.loads(n) for n in networks if n != '']
            if networks:
                context['networks'] = networks
        return context


class AdminLaunchInstance(proj_workflows.LaunchInstance):
    success_url = "horizon:syspanel:instances:index"
    default_steps = (proj_workflows.SelectProjectUser,
                     proj_workflows.SetInstanceDetails,
                     proj_workflows.SetAccessControls,
                     AdminSetNetwork,
                     proj_workflows.VolumeOptions,
                     proj_workflows.PostCreationStep)

    def validate(self, context):
        project_id = context.get('project_id')
        networks = context.get('networks', [])
        for n in networks:
            if n['tenant_id'] != project_id:
                msg = _("Selected network '%s' is not owned "
                        "by the specified project") % n['name']
                # NOTE(amotoki):
                # I tryied to raise WorkflowValidationError according to
                # the docstring of horizon.workflows.base.validate(),
                # but exception seems not to be caught appropriately
                # and exception message passsed was lost.
                # Thus I use messages.error() and then return False.
                #raise exceptions.WorkflowValidationError(msg)
                messages.error(self.request, msg)
                return False
        return True

    def handle(self, request, context):
        custom_script = context.get('customization_script', '')

        # Determine volume mapping options
        if context.get('volume_type', None):
            if(context['delete_on_terminate']):
                del_on_terminate = 1
            else:
                del_on_terminate = 0
            mapping_opts = ("%s::%s"
                            % (context['volume_id'], del_on_terminate))
            dev_mapping = {context['device_name']: mapping_opts}
        else:
            dev_mapping = None

        netids = context.get('networks', None)
        if netids:
            nics = [{"net-id": netid['id'], "v4-fixed-ip": ""}
                    for netid in netids]
        else:
            nics = None

        try:
            # NOTE(amotoki): (well known bug?)
            # project_id specified in launching panel is not referred and
            # an instance is launched in the current project.
            # In addition, api.nova.server_create() does not provide
            # a method to launch an instance by different project/user.
            api.nova.server_create(request,
                                   context['name'],
                                   context['source_id'],
                                   context['flavor'],
                                   context['keypair_id'],
                                   normalize_newlines(custom_script),
                                   context['security_group_ids'],
                                   dev_mapping,
                                   nics=nics,
                                   instance_count=int(context['count']))
            return True
        except:
            exceptions.handle(request)
            return False
