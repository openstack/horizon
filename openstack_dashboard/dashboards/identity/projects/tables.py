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

from django.core.exceptions import ValidationError  # noqa
from django.core.urlresolvers import reverse
from django.template import defaultfilters as filters
from django.utils.http import urlencode
from django.utils.translation import ugettext_lazy as _
from django.utils.translation import ungettext_lazy

from openstack_auth import utils as auth_utils

from horizon import exceptions
from horizon import forms
from horizon import tables
from keystoneclient.exceptions import Conflict  # noqa

from openstack_dashboard import api
from openstack_dashboard import policy


class RescopeTokenToProject(tables.LinkAction):
    name = "rescope"
    verbose_name = _("Set as Active Project")
    url = "switch_tenants"

    def allowed(self, request, project):
        # allow rescoping token to any project the user has a role on,
        # authorized_tenants, and that they are not currently scoped to
        return next((True for proj in request.user.authorized_tenants
                     if proj.id == project.id and
                     project.id != request.user.project_id), False)

    def get_link_url(self, project):
        # redirects to the switch_tenants url which then will redirect
        # back to this page
        dash_url = reverse("horizon:identity:projects:index")
        base_url = reverse(self.url, args=[project.id])
        param = urlencode({"next": dash_url})
        return "?".join([base_url, param])


class UpdateMembersLink(tables.LinkAction):
    name = "users"
    verbose_name = _("Manage Members")
    url = "horizon:identity:projects:update"
    classes = ("ajax-modal",)
    icon = "pencil"
    policy_rules = (("identity", "identity:list_users"),
                    ("identity", "identity:list_roles"))

    def get_link_url(self, project):
        step = 'update_members'
        base_url = reverse(self.url, args=[project.id])
        param = urlencode({"step": step})
        return "?".join([base_url, param])


class UpdateGroupsLink(tables.LinkAction):
    name = "groups"
    verbose_name = _("Modify Groups")
    url = "horizon:identity:projects:update"
    classes = ("ajax-modal",)
    icon = "pencil"
    policy_rules = (("identity", "identity:list_groups"),)

    def allowed(self, request, project):
        return api.keystone.VERSIONS.active >= 3

    def get_link_url(self, project):
        step = 'update_group_members'
        base_url = reverse(self.url, args=[project.id])
        param = urlencode({"step": step})
        return "?".join([base_url, param])


class UsageLink(tables.LinkAction):
    name = "usage"
    verbose_name = _("View Usage")
    url = "horizon:identity:projects:usage"
    icon = "stats"
    policy_rules = (("compute", "compute_extension:simple_tenant_usage:show"),)

    def allowed(self, request, project):
        return request.user.is_superuser


class CreateProject(tables.LinkAction):
    name = "create"
    verbose_name = _("Create Project")
    url = "horizon:identity:projects:create"
    classes = ("ajax-modal",)
    icon = "plus"
    policy_rules = (('identity', 'identity:create_project'),)

    def allowed(self, request, project):
        return api.keystone.keystone_can_edit_project()


class UpdateProject(tables.LinkAction):
    name = "update"
    verbose_name = _("Edit Project")
    url = "horizon:identity:projects:update"
    classes = ("ajax-modal",)
    icon = "pencil"
    policy_rules = (('identity', 'identity:update_project'),)

    def allowed(self, request, project):
        return api.keystone.keystone_can_edit_project()


class ModifyQuotas(tables.LinkAction):
    name = "quotas"
    verbose_name = _("Modify Quotas")
    url = "horizon:identity:projects:update"
    classes = ("ajax-modal",)
    icon = "pencil"
    policy_rules = (('compute', "compute_extension:quotas:update"),)

    def get_link_url(self, project):
        step = 'update_quotas'
        base_url = reverse(self.url, args=[project.id])
        param = urlencode({"step": step})
        return "?".join([base_url, param])


class DeleteTenantsAction(tables.DeleteAction):
    @staticmethod
    def action_present(count):
        return ungettext_lazy(
            u"Delete Project",
            u"Delete Projects",
            count
        )

    @staticmethod
    def action_past(count):
        return ungettext_lazy(
            u"Deleted Project",
            u"Deleted Projects",
            count
        )

    policy_rules = (("identity", "identity:delete_project"),)

    def allowed(self, request, project):
        return api.keystone.keystone_can_edit_project()

    def delete(self, request, obj_id):
        api.keystone.tenant_delete(request, obj_id)

    def handle(self, table, request, obj_ids):
        response = \
            super(DeleteTenantsAction, self).handle(table, request, obj_ids)
        auth_utils.remove_project_cache(request.user.token.unscoped_token)
        return response


class TenantFilterAction(tables.FilterAction):
    def filter(self, table, tenants, filter_string):
        """Really naive case-insensitive search."""
        # FIXME(gabriel): This should be smarter. Written for demo purposes.
        q = filter_string.lower()

        def comp(tenant):
            if q in tenant.name.lower():
                return True
            return False

        return filter(comp, tenants)


class UpdateRow(tables.Row):
    ajax = True

    def get_data(self, request, project_id):
        project_info = api.keystone.tenant_get(request, project_id,
                                               admin=True)
        return project_info


class UpdateCell(tables.UpdateAction):
    def allowed(self, request, project, cell):
        policy_rule = (("identity", "identity:update_project"),)
        return (
            (cell.column.name != 'enabled' or
             request.user.project_id != cell.datum.id) and
            api.keystone.keystone_can_edit_project() and
            policy.check(policy_rule, request))

    def update_cell(self, request, datum, project_id,
                    cell_name, new_cell_value):
        # inline update project info
        try:
            project_obj = datum
            # updating changed value by new value
            setattr(project_obj, cell_name, new_cell_value)
            api.keystone.tenant_update(
                request,
                project_id,
                name=project_obj.name,
                description=project_obj.description,
                enabled=project_obj.enabled)

        except Conflict:
            # Returning a nice error message about name conflict. The message
            # from exception is not that clear for the users.
            message = _("This name is already taken.")
            raise ValidationError(message)
        except Exception:
            exceptions.handle(request, ignore=True)
            return False
        return True


class TenantsTable(tables.DataTable):
    name = tables.Column('name', verbose_name=_('Name'),
                         link=("horizon:identity:projects:detail"),
                         form_field=forms.CharField(max_length=64),
                         update_action=UpdateCell)
    description = tables.Column(lambda obj: getattr(obj, 'description', None),
                                verbose_name=_('Description'),
                                form_field=forms.CharField(
                                    widget=forms.Textarea(attrs={'rows': 4}),
                                    required=False),
                                update_action=UpdateCell)
    id = tables.Column('id', verbose_name=_('Project ID'))
    enabled = tables.Column('enabled', verbose_name=_('Enabled'), status=True,
                            filters=(filters.yesno, filters.capfirst),
                            form_field=forms.BooleanField(
                                label=_('Enabled'),
                                required=False),
                            update_action=UpdateCell)

    def get_project_detail_link(self, project):
        # this method is an ugly monkey patch, needed because
        # the column link method does not provide access to the request
        if policy.check((("identity", "identity:get_project"),),
                        self.request, target={"project": project}):
            return reverse("horizon:identity:projects:detail",
                           args=(project.id,))
        return None

    def __init__(self, request, data=None, needs_form_wrapper=None, **kwargs):
        super(TenantsTable,
              self).__init__(request, data=data,
                             needs_form_wrapper=needs_form_wrapper,
                             **kwargs)
        # see the comment above about ugly monkey patches
        self.columns['name'].get_link_url = self.get_project_detail_link

    class Meta(object):
        name = "tenants"
        verbose_name = _("Projects")
        row_class = UpdateRow
        row_actions = (UpdateMembersLink, UpdateGroupsLink, UpdateProject,
                       UsageLink, ModifyQuotas, DeleteTenantsAction,
                       RescopeTokenToProject)
        table_actions = (TenantFilterAction, CreateProject,
                         DeleteTenantsAction)
        pagination_param = "tenant_marker"
