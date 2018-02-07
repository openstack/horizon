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

from django.utils.translation import ugettext_lazy as _

from horizon import exceptions
from horizon import forms
from horizon import workflows

from openstack_dashboard import api
from openstack_dashboard.dashboards.admin.aggregates import constants


class SetAggregateInfoAction(workflows.Action):
    name = forms.CharField(label=_("Name"),
                           max_length=255)

    availability_zone = forms.CharField(label=_("Availability Zone"),
                                        required=False,
                                        max_length=255)

    class Meta(object):
        name = _("Host Aggregate Information")
        help_text = _("Host aggregates divide an availability zone into "
                      "logical units by grouping together hosts. Create a "
                      "host aggregate then select the hosts contained in it.")
        slug = "set_aggregate_info"

    def clean(self):
        cleaned_data = super(SetAggregateInfoAction, self).clean()
        name = cleaned_data.get('name', '')

        try:
            aggregates = api.nova.aggregate_details_list(self.request)
        except Exception:
            msg = _('Unable to get host aggregate list')
            exceptions.check_message(["Connection", "refused"], msg)
            raise
        if aggregates is not None:
            for aggregate in aggregates:
                if aggregate.name.lower() == name.lower():
                    raise forms.ValidationError(
                        _('The name "%s" is already used by '
                          'another host aggregate.')
                        % name
                    )
        return cleaned_data


class SetAggregateInfoStep(workflows.Step):
    action_class = SetAggregateInfoAction
    contributes = ("availability_zone",
                   "name")


class AddHostsToAggregateAction(workflows.MembershipAction):
    def __init__(self, request, *args, **kwargs):
        super(AddHostsToAggregateAction, self).__init__(request,
                                                        *args,
                                                        **kwargs)
        err_msg = _('Unable to get the available hosts')

        default_role_field_name = self.get_default_role_field_name()
        self.fields[default_role_field_name] = forms.CharField(required=False)
        self.fields[default_role_field_name].initial = 'member'

        field_name = self.get_member_field_name('member')
        self.fields[field_name] = forms.MultipleChoiceField(required=False)

        services = []
        try:
            services = api.nova.service_list(request, binary='nova-compute')
        except Exception:
            exceptions.handle(request, err_msg)

        host_names = [s.host for s in services]
        host_names.sort()

        self.fields[field_name].choices = \
            [(host_name, host_name) for host_name in host_names]

    class Meta(object):
        name = _("Manage Hosts within Aggregate")
        slug = "add_host_to_aggregate"


class ManageAggregateHostsAction(workflows.MembershipAction):
    def __init__(self, request, *args, **kwargs):
        super(ManageAggregateHostsAction, self).__init__(request,
                                                         *args,
                                                         **kwargs)
        err_msg = _('Unable to get the available hosts')

        default_role_field_name = self.get_default_role_field_name()
        self.fields[default_role_field_name] = forms.CharField(required=False)
        self.fields[default_role_field_name].initial = 'member'

        field_name = self.get_member_field_name('member')
        self.fields[field_name] = forms.MultipleChoiceField(required=False)

        aggregate_id = self.initial['id']
        aggregate = api.nova.aggregate_get(request, aggregate_id)
        current_aggregate_hosts = aggregate.hosts

        services = []
        try:
            services = api.nova.service_list(request, binary='nova-compute')
        except Exception:
            exceptions.handle(request, err_msg)

        host_names = [s.host for s in services]
        host_names.sort()

        self.fields[field_name].choices = \
            [(host_name, host_name) for host_name in host_names]

        self.fields[field_name].initial = current_aggregate_hosts

    class Meta(object):
        name = _("Manage Hosts within Aggregate")


class AddHostsToAggregateStep(workflows.UpdateMembersStep):
    action_class = AddHostsToAggregateAction
    help_text = _("Add hosts to this aggregate. Hosts can be in multiple "
                  "aggregates.")
    available_list_title = _("All available hosts")
    members_list_title = _("Selected hosts")
    no_available_text = _("No hosts found.")
    no_members_text = _("No host selected.")
    show_roles = False
    contributes = ("hosts_aggregate",)

    def contribute(self, data, context):
        if data:
            member_field_name = self.get_member_field_name('member')
            context['hosts_aggregate'] = data.get(member_field_name, [])
        return context


class ManageAggregateHostsStep(workflows.UpdateMembersStep):
    action_class = ManageAggregateHostsAction
    help_text = _("Add hosts to this aggregate or remove hosts from it. "
                  "Hosts can be in multiple aggregates.")
    available_list_title = _("All Available Hosts")
    members_list_title = _("Selected Hosts")
    no_available_text = _("No Hosts found.")
    no_members_text = _("No Host selected.")
    show_roles = False
    depends_on = ("id",)
    contributes = ("hosts_aggregate",)

    def contribute(self, data, context):
        if data:
            member_field_name = self.get_member_field_name('member')
            context['hosts_aggregate'] = data.get(member_field_name, [])
        return context


class CreateAggregateWorkflow(workflows.Workflow):
    slug = "create_aggregate"
    name = _("Create Host Aggregate")
    finalize_button_name = _("Create Host Aggregate")
    success_message = _('Created new host aggregate "%s".')
    failure_message = _('Unable to create host aggregate "%s".')
    success_url = constants.AGGREGATES_INDEX_URL
    default_steps = (SetAggregateInfoStep, AddHostsToAggregateStep)

    def format_status_message(self, message):
        return message % self.context['name']

    def handle(self, request, context):
        try:
            self.object = \
                api.nova.aggregate_create(
                    request,
                    name=context['name'],
                    availability_zone=context['availability_zone'] or None)
        except Exception:
            exceptions.handle(request, _('Unable to create host aggregate.'))
            return False

        context_hosts_aggregate = context['hosts_aggregate']
        for host in context_hosts_aggregate:
            try:
                api.nova.add_host_to_aggregate(request, self.object.id, host)
            except Exception:
                exceptions.handle(
                    request, _('Error adding Hosts to the aggregate.'))
                # Host aggregate itself has been created successfully,
                # so we return True here
                return True

        return True


class ManageAggregateHostsWorkflow(workflows.Workflow):
    slug = "manage_hosts_aggregate"
    name = _("Add/Remove Hosts to Aggregate")
    finalize_button_name = _("Save")
    success_message = _('The Aggregate was updated.')
    failure_message = _('Unable to update the aggregate.')
    success_url = constants.AGGREGATES_INDEX_URL
    default_steps = (ManageAggregateHostsStep, )

    def handle(self, request, context):
        aggregate_id = context['id']
        aggregate = api.nova.aggregate_get(request, aggregate_id)
        current_aggregate_hosts = set(aggregate.hosts)
        context_hosts_aggregate = set(context['hosts_aggregate'])
        removed_hosts = current_aggregate_hosts - context_hosts_aggregate
        added_hosts = context_hosts_aggregate - current_aggregate_hosts
        try:
            for host in removed_hosts:
                api.nova.remove_host_from_aggregate(request,
                                                    aggregate_id,
                                                    host)
            for host in added_hosts:
                api.nova.add_host_to_aggregate(request, aggregate_id, host)
        except Exception:
            exceptions.handle(
                request, _('Error when adding or removing hosts.'))
            return False
        return True
