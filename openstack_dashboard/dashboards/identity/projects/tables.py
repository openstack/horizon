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

from django.core.urlresolvers import reverse
from django.template import defaultfilters as filters
from django.utils.http import urlencode
from django.utils.translation import ugettext_lazy as _
from django.utils.translation import ungettext_lazy

from horizon import forms
from horizon import tables

from openstack_dashboard import api
from openstack_dashboard import policy
from openstack_dashboard.usage import quotas


class RescopeTokenToProject(tables.LinkAction):
    name = "rescope"
    verbose_name = _("Set as Active Project")
    url = "switch_tenants"

    def allowed(self, request, project):
        # allow rescoping token to any project the user has a role on,
        # authorized_tenants, and that they are not currently scoped to
        return next((True for proj in request.user.authorized_tenants
                     if proj.id == project.id and
                     project.id != request.user.project_id and
                     project.enabled), False)

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

    def allowed(self, request, project):
        if api.keystone.is_multi_domain_enabled():
            # domain admin or cloud admin = True
            # project admin or member = False
            return api.keystone.is_domain_admin(request)
        else:
            return super(UpdateMembersLink, self).allowed(request, project)


class UpdateGroupsLink(tables.LinkAction):
    name = "groups"
    verbose_name = _("Modify Groups")
    url = "horizon:identity:projects:update"
    classes = ("ajax-modal",)
    icon = "pencil"
    policy_rules = (("identity", "identity:list_groups"),)

    def allowed(self, request, project):
        if api.keystone.is_multi_domain_enabled():
            # domain admin or cloud admin = True
            # project admin or member = False
            return api.keystone.is_domain_admin(request)
        else:
            return super(UpdateGroupsLink, self).allowed(request, project)

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
    policy_rules = (("compute", "os_compute_api:os-simple-tenant-usage:show"),)

    def allowed(self, request, project):
        return (request.user.is_superuser and
                api.base.is_service_enabled(request, 'compute'))


class CreateProject(tables.LinkAction):
    name = "create"
    verbose_name = _("Create Project")
    url = "horizon:identity:projects:create"
    classes = ("ajax-modal",)
    icon = "plus"
    policy_rules = (('identity', 'identity:create_project'),)

    def allowed(self, request, project):
        if api.keystone.is_multi_domain_enabled():
            # domain admin or cloud admin = True
            # project admin or member = False
            return api.keystone.is_domain_admin(request)
        else:
            return api.keystone.keystone_can_edit_project()


class UpdateProject(policy.PolicyTargetMixin, tables.LinkAction):
    name = "update"
    verbose_name = _("Edit Project")
    url = "horizon:identity:projects:update"
    classes = ("ajax-modal",)
    icon = "pencil"
    policy_rules = (('identity', 'identity:update_project'),)
    policy_target_attrs = (("target.project.domain_id", "domain_id"),)

    def allowed(self, request, project):
        if api.keystone.is_multi_domain_enabled():
            # domain admin or cloud admin = True
            # project admin or member = False
            return api.keystone.is_domain_admin(request)
        else:
            return api.keystone.keystone_can_edit_project()


class ModifyQuotas(tables.LinkAction):
    name = "quotas"
    verbose_name = _("Modify Quotas")
    url = "horizon:identity:projects:update"
    classes = ("ajax-modal",)
    icon = "pencil"
    policy_rules = (('compute', "os_compute_api:os-quota-sets:update"),)

    def allowed(self, request, datum):
        if api.keystone.VERSIONS.active < 3:
            return True
        else:
            return (api.keystone.is_cloud_admin(request) and
                    quotas.enabled_quotas(request))

    def get_link_url(self, project):
        step = 'update_quotas'
        base_url = reverse(self.url, args=[project.id])
        param = urlencode({"step": step})
        return "?".join([base_url, param])


class DeleteTenantsAction(policy.PolicyTargetMixin, tables.DeleteAction):
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
    policy_target_attrs = ("target.project.domain_id", "domain_id"),

    def allowed(self, request, project):
        if api.keystone.is_multi_domain_enabled() \
                and not api.keystone.is_domain_admin(request):
            return False
        return api.keystone.keystone_can_edit_project()

    def delete(self, request, obj_id):
        api.keystone.tenant_delete(request, obj_id)

    def handle(self, table, request, obj_ids):
        response = \
            super(DeleteTenantsAction, self).handle(table, request, obj_ids)
        return response


class TenantFilterAction(tables.FilterAction):
    if api.keystone.VERSIONS.active < 3:
        filter_type = "query"
    else:
        filter_type = "server"
        filter_choices = (('name', _("Project Name ="), True),
                          ('id', _("Project ID ="), True),
                          ('enabled', _("Enabled ="), True, _('e.g. Yes/No')))


class UpdateRow(tables.Row):
    ajax = True

    def get_data(self, request, project_id):
        project_info = api.keystone.tenant_get(request, project_id,
                                               admin=True)
        return project_info


class TenantsTable(tables.DataTable):
    name = tables.WrappingColumn('name', verbose_name=_('Name'),
                                 link=("horizon:identity:projects:detail"),
                                 form_field=forms.CharField(max_length=64))
    description = tables.Column(lambda obj: getattr(obj, 'description', None),
                                verbose_name=_('Description'),
                                form_field=forms.CharField(
                                    widget=forms.Textarea(attrs={'rows': 4}),
                                    required=False))
    id = tables.Column('id', verbose_name=_('Project ID'))

    if api.keystone.VERSIONS.active >= 3:
        domain_name = tables.Column(
            'domain_name', verbose_name=_('Domain Name'))

    enabled = tables.Column('enabled', verbose_name=_('Enabled'), status=True,
                            filters=(filters.yesno, filters.capfirst),
                            form_field=forms.BooleanField(
                                label=_('Enabled'),
                                required=False))

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
