from django.core.urlresolvers import reverse  # noqa
from django.utils.http import urlencode  # noqa
from django.utils.translation import ugettext_lazy as _  # noqa

from horizon import tables

from openstack_dashboard import api
from openstack_dashboard.api import keystone


class ViewMembersLink(tables.LinkAction):
    name = "users"
    verbose_name = _("Modify Users")
    url = "horizon:admin:projects:update"
    classes = ("ajax-modal", "btn-edit")
    policy_rules = (("identity", "identity:list_users"),
                    ("identity", "identity:list_roles"))

    def get_link_url(self, project):
        step = 'update_members'
        base_url = reverse(self.url, args=[project.id])
        param = urlencode({"step": step})
        return "?".join([base_url, param])


class ViewGroupsLink(tables.LinkAction):
    name = "groups"
    verbose_name = _("Modify Groups")
    url = "horizon:admin:projects:update"
    classes = ("ajax-modal", "btn-edit")

    def allowed(self, request, project):
        return keystone.VERSIONS.active >= 3

    def get_link_url(self, project):
        step = 'update_group_members'
        base_url = reverse(self.url, args=[project.id])
        param = urlencode({"step": step})
        return "?".join([base_url, param])


class UsageLink(tables.LinkAction):
    name = "usage"
    verbose_name = _("View Usage")
    url = "horizon:admin:projects:usage"
    classes = ("btn-stats",)
    policy_rules = (("compute", "compute_extension:simple_tenant_usage:show"),)


class CreateProject(tables.LinkAction):
    name = "create"
    verbose_name = _("Create Project")
    url = "horizon:admin:projects:create"
    classes = ("btn-launch", "ajax-modal",)
    policy_rules = (('identity', 'identity:create_project'),)

    def allowed(self, request, project):
        return api.keystone.keystone_can_edit_project()


class UpdateProject(tables.LinkAction):
    name = "update"
    verbose_name = _("Edit Project")
    url = "horizon:admin:projects:update"
    classes = ("ajax-modal", "btn-edit")
    policy_rules = (('identity', 'identity:update_project'),)

    def allowed(self, request, project):
        return api.keystone.keystone_can_edit_project()


class ModifyQuotas(tables.LinkAction):
    name = "quotas"
    verbose_name = _("Modify Quotas")
    url = "horizon:admin:projects:update"
    classes = ("ajax-modal", "btn-edit")
    policy_rules = (('compute', "compute_extension:quotas:update"),)

    def get_link_url(self, project):
        step = 'update_quotas'
        base_url = reverse(self.url, args=[project.id])
        param = urlencode({"step": step})
        return "?".join([base_url, param])


class DeleteTenantsAction(tables.DeleteAction):
    data_type_singular = _("Project")
    data_type_plural = _("Projects")
    policy_rules = (("identity", "identity:delete_project"),)

    def allowed(self, request, project):
        return api.keystone.keystone_can_edit_project()

    def delete(self, request, obj_id):
        api.keystone.tenant_delete(request, obj_id)


class TenantFilterAction(tables.FilterAction):
    def filter(self, table, tenants, filter_string):
        """ Really naive case-insensitive search. """
        # FIXME(gabriel): This should be smarter. Written for demo purposes.
        q = filter_string.lower()

        def comp(tenant):
            if q in tenant.name.lower():
                return True
            return False

        return filter(comp, tenants)


class TenantsTable(tables.DataTable):
    name = tables.Column('name', verbose_name=_('Name'))
    description = tables.Column(lambda obj: getattr(obj, 'description', None),
                                verbose_name=_('Description'))
    id = tables.Column('id', verbose_name=_('Project ID'))
    enabled = tables.Column('enabled', verbose_name=_('Enabled'), status=True)

    class Meta:
        name = "tenants"
        verbose_name = _("Projects")
        row_actions = (ViewMembersLink, ViewGroupsLink, UpdateProject,
                       UsageLink, ModifyQuotas, DeleteTenantsAction)
        table_actions = (TenantFilterAction, CreateProject,
                         DeleteTenantsAction)
        pagination_param = "tenant_marker"
