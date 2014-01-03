# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright 2013 Hewlett-Packard Development Company, L.P.
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

import logging

from django.conf import settings
from django.core.urlresolvers import reverse
from django.utils.translation import ugettext_lazy as _

from horizon import exceptions
from horizon import forms
from horizon import workflows

from openstack_dashboard import api

from openstack_dashboard.dashboards.admin.domains import constants

LOG = logging.getLogger(__name__)


class CreateDomainInfoAction(workflows.Action):
    name = forms.CharField(label=_("Name"),
                           required=True)
    description = forms.CharField(widget=forms.widgets.Textarea(),
                                  label=_("Description"),
                                  required=False)
    enabled = forms.BooleanField(label=_("Enabled"),
                                 required=False,
                                 initial=True)

    class Meta:
        name = _("Domain Info")
        slug = "create_domain"
        help_text = _("From here you can create a new domain to organize "
                      "projects, groups and users.")


class CreateDomainInfo(workflows.Step):
    action_class = CreateDomainInfoAction
    contributes = ("domain_id",
                   "name",
                   "description",
                   "enabled")


class UpdateDomainGroupsAction(workflows.MembershipAction):
    def __init__(self, request, *args, **kwargs):
        super(UpdateDomainGroupsAction, self).__init__(request,
                                                       *args,
                                                       **kwargs)
        err_msg = _('Unable to retrieve group list. Please try again later.')
        domain_id = ''
        if 'domain_id' in args[0]:
            domain_id = args[0]['domain_id']

        # Get the default role
        try:
            default_role = api.keystone.get_default_role(self.request)
            # Default role is necessary to add members to a domain
            if default_role is None:
                default = getattr(settings,
                                  "OPENSTACK_KEYSTONE_DEFAULT_ROLE", None)
                msg = _('Could not find default role "%s" in Keystone') % \
                        default
                raise exceptions.NotFound(msg)
        except Exception:
            exceptions.handle(self.request,
                              err_msg,
                              redirect=reverse(constants.DOMAINS_INDEX_URL))
        default_role_name = self.get_default_role_field_name()
        self.fields[default_role_name] = forms.CharField(required=False)
        self.fields[default_role_name].initial = default_role.id

        # Get list of available groups
        all_groups = []
        try:
            all_groups = api.keystone.group_list(request,
                                                 domain=domain_id)
        except Exception:
            exceptions.handle(request, err_msg)
        groups_list = [(group.id, group.name) for group in all_groups]

        # Get list of roles
        role_list = []
        try:
            role_list = api.keystone.role_list(request)
        except Exception:
            exceptions.handle(request,
                              err_msg,
                              redirect=reverse(constants.DOMAINS_INDEX_URL))
        for role in role_list:
            field_name = self.get_member_field_name(role.id)
            label = role.name
            self.fields[field_name] = forms.MultipleChoiceField(required=False,
                                                                label=label)
            self.fields[field_name].choices = groups_list
            self.fields[field_name].initial = []

        # Figure out groups & roles
        if domain_id:
            for group in all_groups:
                try:
                    roles = api.keystone.roles_for_group(self.request,
                                                         group=group.id,
                                                         domain=domain_id)
                except Exception:
                    exceptions.handle(request,
                                      err_msg,
                                      redirect=reverse(
                                          constants.DOMAINS_INDEX_URL))
                for role in roles:
                    field_name = self.get_member_field_name(role.id)
                    self.fields[field_name].initial.append(group.id)

    class Meta:
        name = _("Domain Groups")
        slug = constants.DOMAIN_GROUP_MEMBER_SLUG


class UpdateDomainGroups(workflows.UpdateMembersStep):
    action_class = UpdateDomainGroupsAction
    available_list_title = _("All Groups")
    members_list_title = _("Domain Groups")
    no_available_text = _("No groups found.")
    no_members_text = _("No groups.")

    def contribute(self, data, context):
        if data:
            try:
                roles = api.keystone.role_list(self.workflow.request)
            except Exception:
                exceptions.handle(self.workflow.request,
                                  _('Unable to retrieve role list.'))

            post = self.workflow.request.POST
            for role in roles:
                field = self.get_member_field_name(role.id)
                context[field] = post.getlist(field)
        return context


class CreateDomain(workflows.Workflow):
    slug = "create_domain"
    name = _("Create Domain")
    finalize_button_name = _("Create Domain")
    success_message = _('Created new domain "%s".')
    failure_message = _('Unable to create domain "%s".')
    success_url = constants.DOMAINS_INDEX_URL
    default_steps = (CreateDomainInfo, )

    def format_status_message(self, message):
        return message % self.context.get('name', 'unknown domain')

    def handle(self, request, data):
        # create the domain
        try:
            LOG.info('Creating domain with name "%s"' % data['name'])
            desc = data['description']
            api.keystone.domain_create(request,
                                       name=data['name'],
                                       description=desc,
                                       enabled=data['enabled'])
        except Exception:
            exceptions.handle(request, ignore=True)
            return False
        return True


class UpdateDomainInfoAction(CreateDomainInfoAction):

    class Meta:
        name = _("Domain Info")
        slug = 'update_domain'
        help_text = _("From here you can edit the domain details.")


class UpdateDomainInfo(workflows.Step):
    action_class = UpdateDomainInfoAction
    depends_on = ("domain_id",)
    contributes = ("name",
                   "description",
                   "enabled")


class UpdateDomain(workflows.Workflow):
    slug = "update_domain"
    name = _("Edit Domain")
    finalize_button_name = _("Save")
    success_message = _('Modified domain "%s".')
    failure_message = _('Unable to modify domain "%s".')
    success_url = constants.DOMAINS_INDEX_URL
    default_steps = (UpdateDomainInfo,
                     UpdateDomainGroups)

    def format_status_message(self, message):
        return message % self.context.get('name', 'unknown domain')

    def handle(self, request, data):
        domain_id = data.pop('domain_id')

        try:
            LOG.info('Updating domain with name "%s"' % data['name'])
            api.keystone.domain_update(request,
                                       domain_id=domain_id,
                                       name=data['name'],
                                       description=data['description'],
                                       enabled=data['enabled'])
        except Exception:
            exceptions.handle(request, ignore=True)
            return False

        # update domain groups
        groups_to_modify = 0
        member_step = self.get_step(constants.DOMAIN_GROUP_MEMBER_SLUG)
        try:
            # Get our role options
            available_roles = api.keystone.role_list(request)
            # Get the groups currently associated with this domain so we
            # can diff against it.
            domain_groups = api.keystone.group_list(request,
                                                    domain=domain_id)
            groups_to_modify = len(domain_groups)
            for group in domain_groups:
                # Check if there have been any changes in the roles of
                # Existing domain members.
                current_roles = api.keystone.roles_for_group(
                    self.request,
                    group=group.id,
                    domain=domain_id)
                current_role_ids = [role.id for role in current_roles]
                for role in available_roles:
                    # Check if the group is in the list of groups with
                    # this role.
                    field_name = member_step.get_member_field_name(role.id)
                    if group.id in data[field_name]:
                        # Add it if necessary
                        if role.id not in current_role_ids:
                            # group role has changed
                            api.keystone.add_group_role(
                                request,
                                role=role.id,
                                group=group.id,
                                domain=domain_id)
                        else:
                            # Group role is unchanged, so remove it from
                            # the remaining roles list to avoid removing it
                            # later
                            index = current_role_ids.index(role.id)
                            current_role_ids.pop(index)

                # Revoke any removed roles.
                for id_to_delete in current_role_ids:
                    api.keystone.remove_group_role(request,
                                                   role=id_to_delete,
                                                   group=group.id,
                                                   domain=domain_id)
                groups_to_modify -= 1

            # Grant new roles on the domain.
            for role in available_roles:
                field_name = member_step.get_member_field_name(role.id)
                # Count how many groups may be added for error handling.
                groups_to_modify += len(data[field_name])
            for role in available_roles:
                groups_added = 0
                field_name = member_step.get_member_field_name(role.id)
                for group_id in data[field_name]:
                    if not filter(lambda x: group_id == x.id, domain_groups):
                        api.keystone.add_group_role(request,
                                                    role=role.id,
                                                    group=group_id,
                                                    domain=domain_id)
                    groups_added += 1
                groups_to_modify -= groups_added
        except Exception:
            exceptions.handle(request, _('Failed to modify %s domain groups.'
                                         % groups_to_modify))
            return True

        return True
