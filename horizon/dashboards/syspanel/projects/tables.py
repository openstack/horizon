import logging

from django.core.urlresolvers import reverse
from django.utils.translation import ugettext_lazy as _

from horizon import api
from horizon import tables

from ..users.tables import UsersTable

from django.conf import settings
from horizon.api.base import url_for
from horizon import exceptions
from rgwauthAPI import RadosGW as RGW

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
        use_radosgw_auth = getattr(settings, 'SWIFT_USE_RADOSGW_AUTH', False)
        sync_radosgw_auth = getattr(settings, 'SYNC_KEYSTONE_RADOSGW_AUTH', False)
        if use_radosgw_auth and sync_radosgw_auth:
            endpoint = url_for(request, 'object-store')
            try:
                LOG.debug('Radosgw remove user %s from endpoint: %s'
                        % (obj_id, endpoint))
                RGW(obj_id, 'admin', authUrl=endpoint).rmUser()
            except:
                raise exceptions.RadosgwExceptions('Remove radosgw:user failed.')
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
    id = tables.Column('id', verbose_name=_('Id'))
    name = tables.Column('name', verbose_name=_('Name'))
    description = tables.Column(lambda obj: getattr(obj, 'description', None),
                                verbose_name=_('Description'))
    enabled = tables.Column('enabled', verbose_name=_('Enabled'), status=True)

    class Meta:
        name = "tenants"
        verbose_name = _("Projects")
        row_actions = (EditLink, UsageLink, ViewMembersLink, ModifyQuotasLink,
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
        use_radosgw_auth = getattr(settings, 'SWIFT_USE_RADOSGW_AUTH', False)
        sync_radosgw_auth = getattr(settings, 'SYNC_KEYSTONE_RADOSGW_AUTH', False)
        if use_radosgw_auth and sync_radosgw_auth:
            endpoint = url_for(request, 'object-store')
            uid, subuser = tenant_id, user_id
            try:
                LOG.debug('Radosgw remove subuser %s:%s from endpoint: %s'
                        % (uid, subuser, endpoint))
                RGW(uid, subuser, endpoint).rmSubuser()
            except:
                redirect = reverse("horizon:syspanel:projects:users", args=(tenant_id,))
                exceptions.handle(request, _('Remove user failed.'), redirect=redirect)
        api.keystone.remove_tenant_user(request, tenant_id, user_id)

class TenantUsersTable(UsersTable):
    class Meta:
        name = "tenant_users"
        verbose_name = _("Users For Project")
        table_actions = (RemoveUserAction,)
        row_actions = (RemoveUserAction,)


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
