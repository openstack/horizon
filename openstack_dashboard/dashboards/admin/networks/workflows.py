# Copyright 2012 NEC Corporation
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

from django.core.urlresolvers import reverse

from openstack_dashboard.dashboards.admin.networks import forms \
    as networks_forms
from openstack_dashboard.dashboards.project.networks \
    import workflows as network_workflows


class CreateNetworkInfoAction(network_workflows.CreateNetworkInfoAction):

    def __init__(self, request, context, *args, **kwargs):
        self.create_network_form = context.get('create_network_form')
        self.base_fields = self.create_network_form.base_fields

        super(CreateNetworkInfoAction, self).__init__(
            request, context, *args, **kwargs)
        self.fields = self.create_network_form.fields

    def clean(self):
        self.create_network_form.cleaned_data = super(
            CreateNetworkInfoAction, self).clean()
        self.create_network_form._changed_data = self.changed_data
        self.create_network_form._errors = self.errors
        return self.create_network_form.clean()

    class Meta(object):
        name = network_workflows.CreateNetworkInfoAction.name
        help_text = network_workflows.CreateNetworkInfoAction.help_text


class CreateNetworkInfo(network_workflows.CreateNetworkInfo):
    action_class = CreateNetworkInfoAction
    contributes = ("net_name", "admin_state", "with_subnet")

    def __init__(self, workflow):
        self.contributes = tuple(workflow.create_network_form.fields.keys())
        super(CreateNetworkInfo, self).__init__(workflow)

    def prepare_action_context(self, request, context):
        context = super(CreateNetworkInfo, self).prepare_action_context(
            request, context)
        context['create_network_form'] = self.workflow.create_network_form
        return context


class CreateNetwork(network_workflows.CreateNetwork):
    default_steps = (CreateNetworkInfo,
                     network_workflows.CreateSubnetInfo,
                     network_workflows.CreateSubnetDetail)

    def __init__(self, request=None, context_seed=None, entry_point=None,
                 *args, **kwargs):
        self.create_network_form = networks_forms.CreateNetwork(
            request, *args, **kwargs)
        super(CreateNetwork, self).__init__(
            request=request,
            context_seed=context_seed,
            entry_point=entry_point,
            *args, **kwargs)

    def get_success_url(self):
        return reverse("horizon:admin:networks:index")

    def get_failure_url(self):
        return reverse("horizon:admin:networks:index")

    def _create_network(self, request, data):
        network = self.create_network_form.handle(request, data)
        # Replicate logic from parent CreateNetwork._create_network
        if network:
            self.context['net_id'] = network.id
            self.context['net_name'] = network.name
        return network
