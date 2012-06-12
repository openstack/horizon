import logging

from django.core.urlresolvers import reverse
from django.utils.translation import ugettext_lazy as _

from horizon import api
from horizon import exceptions
from horizon import tables

from ..users.tables import UsersTable


LOG = logging.getLogger(__name__)


class ModifyQuotasLink(tables.LinkAction):
    name = "quotas"
    verbose_name = _("Modify Quotas")
    url = "horizon:syspanel:projects:quotas"
    classes = ("ajax-modal", "btn-edit")


class ViewMembersLink(tables.LinkAction):
    name = "users"
    verbose_name = _("Modify Users")
    url = "horizon:syspanel:projects:users"
    classes = ("btn-download",)


class UsageLink(tables.LinkAction):
    name = "usage"
    verbose_name = _("View Usage")
    url = "horizon:syspanel:projects:usage"
    classes = ("btn-stats",)


class EditLink(tables.LinkAction):
    name = "update"
    verbose_name = _("Edit Project")
    url = "horizon:syspanel:projects:update"
    classes = ("ajax-modal", "btn-edit")


class CreateLink(tables.LinkAction):
    name = "create"
    verbose_name = _("Create New Project")
    url = "horizon:syspanel:projects:create"
    classes = ("ajax-modal",)


class DeleteTenantsAction(tables.DeleteAction):
    data_type_singular = _("Project")
    data_type_plural = _("Projects")

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
        row_actions = (ViewMembersLink, EditLink, UsageLink, ModifyQuotasLink,
                       DeleteTenantsAction)
        table_actions = (TenantFilterAction, CreateLink, DeleteTenantsAction)


class RemoveUserAction(tables.BatchAction):
    name = "remove_user"
    action_present = _("Remove")
    action_past = _("Removed")
    data_type_singular = _("User")
    data_type_plural = _("Users")
    classes = ('btn-danger',)

    def action(self, request, user_id):
        tenant_id = self.table.kwargs['tenant_id']
        api.keystone.remove_tenant_user(request, tenant_id, user_id)


class ProjectUserRolesColumn(tables.Column):
    def get_raw_data(self, user):
        request = self.table._meta.request
        try:
            roles = api.keystone.roles_for_user(request,
                                                user.id,
                                                self.table.kwargs["tenant_id"])
        except:
            roles = []
            exceptions.handle(request,
                              _("Unable to retrieve role information."))
        return ", ".join([role.name for role in roles])


class TenantUsersTable(UsersTable):
    roles = ProjectUserRolesColumn("roles", verbose_name=_("Roles"))

    class Meta:
        name = "tenant_users"
        verbose_name = _("Users For Project")
        table_actions = (RemoveUserAction,)
        row_actions = (RemoveUserAction,)
        columns = ("name", "email", "id", "roles", "enabled")


class AddUserAction(tables.LinkAction):
    name = "add_user"
    verbose_name = _("Add To Project")
    url = "horizon:syspanel:projects:add_user"
    classes = ('ajax-modal',)

    def get_link_url(self, user):
        tenant_id = self.table.kwargs['tenant_id']
        return reverse(self.url, args=(tenant_id, user.id))


class AddUsersTable(UsersTable):
    class Meta:
        name = "add_users"
        verbose_name = _("Add New Users")
        table_actions = ()
        row_actions = (AddUserAction,)
        columns = ("name", "email", "id", "enabled")
