# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

from django import urls
from django.utils.translation import ugettext_lazy as _

from horizon import forms
from horizon import tables

from openstack_dashboard import policy


def get_project_name(datum):
    if "project" in datum.scope:
        if "name" in datum.scope["project"]:
            return datum.scope["project"]["name"]
        return datum.scope["project"]["id"]


def get_project_link(datum, request):
    if "project" not in datum.scope:
        return
    if policy.check((("identity", "identity:get_project"),),
                    request, target={"project": datum}):
        return urls.reverse("horizon:identity:projects:detail",
                            args=(datum.scope["project"]["id"],))


def get_domain_name(datum):
    if "domain" in datum.scope:
        if "name" in datum.scope["domain"]:
            return datum.scope["domain"]["name"]
        return datum.scope["domain"]["id"]


def get_system_scope(datum):
    if "system" in datum.scope:
        return ', '.join(datum.scope["system"].keys())


def get_role_name(datum):
    role_name = datum.role["name"] if "name" in datum.role \
        else datum.role["id"]

    if hasattr(datum, "group"):
        # This is a role assignment through a group
        group_name = datum.group["name"] if "name" in datum.group \
            else datum.group["id"]
        role_name = _("%(role)s  (through group %(group)s)") % {
            'role': role_name, 'group': group_name}

    return role_name


class RoleAssignmentsTable(tables.DataTable):

    project = tables.WrappingColumn(get_project_name,
                                    verbose_name=_('Project'),
                                    link=get_project_link,
                                    form_field=forms.CharField(max_length=64))

    domain = tables.WrappingColumn(get_domain_name,
                                   verbose_name=_('Domain'),
                                   form_field=forms.CharField(max_length=64))

    system = tables.WrappingColumn(get_system_scope,
                                   verbose_name=_('System Scope'),
                                   form_field=forms.CharField(max_length=64))

    role = tables.Column(get_role_name,
                         verbose_name=_('Role'),
                         form_field=forms.CharField(
                             widget=forms.Textarea(attrs={'rows': 4}),
                             required=False))

    def get_object_id(self, datum):
        """Identifier of the role assignment."""

        # Role assignment doesn't have identifier so one will be created
        # from the identifier of scope, user and role. This will guaranty the
        # unicity.
        scope_id = ""
        if "project" in datum.scope:
            scope_id = datum.scope["project"]["id"]
        elif "domain" in datum.scope:
            scope_id = datum.scope["domain"]["id"]

        assignee_id = ""
        if hasattr(datum, "user"):
            assignee_id = datum.user["id"]
        elif hasattr(datum, "group"):
            assignee_id = datum.group["id"]

        return "%s%s%s" % (assignee_id, datum.role["id"], scope_id)

    class Meta(object):
        name = "roleassignmentstable"
        verbose_name = _("Role assignments")
