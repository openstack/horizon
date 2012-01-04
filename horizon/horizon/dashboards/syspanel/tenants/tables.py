import logging

from django import shortcuts
from django.contrib import messages
from django.utils.translation import ugettext_lazy as _

from horizon import api
from horizon import tables


LOG = logging.getLogger(__name__)


class ModifyQuotasLink(tables.LinkAction):
    name = "quotas"
    verbose_name = _("Modify Quotas")
    url = "horizon:syspanel:tenants:quotas"
    attrs = {"class": "ajax-modal"}


class ViewMembersLink(tables.LinkAction):
    name = "users"
    verbose_name = _("View Members")
    url = "horizon:syspanel:tenants:users"


class EditLink(tables.LinkAction):
    name = "update"
    verbose_name = _("Edit")
    url = "horizon:syspanel:tenants:update"
    attrs = {"class": "ajax-modal"}


class CreateLink(tables.LinkAction):
    name = "create"
    verbose_name = _("Create New Tenant")
    url = "horizon:syspanel:tenants:create"
    attrs = {"class": "ajax-modal btn small"}


class DeleteTenantsAction(tables.Action):
    name = "delete"
    verbose_name = _("Delete")
    verbose_name_plural = _("Delete Tenants")
    classes = ("danger",)

    def handle(self, data_table, request, object_ids):
        failures = 0
        deleted = []
        for obj_id in object_ids:
            LOG.info('Deleting tenant with id "%s"' % obj_id)
            try:
                api.keystone.tenant_delete(request, obj_id)
                deleted.append(obj_id)
            except Exception, e:
                failures += 1
                messages.error(request, _("Error deleting tenant: %s") % e)
                LOG.exception("Error deleting tenant.")
        if failures:
            messages.info(request, _("Deleted the following tenant: %s")
                                     % ", ".join(deleted))
        else:
            messages.success(request, _("Successfully deleted tenant: %s")
                                        % ", ".join(deleted))
        return shortcuts.redirect('horizon:syspanel:tenants:index')


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
    description = tables.Column("description", verbose_name=_('Description'))
    enabled = tables.Column('enabled', verbose_name=_('Enabled'), status=True)

    class Meta:
        name = "tenants"
        verbose_name = _("Tenants")
        row_actions = (EditLink, ViewMembersLink, ModifyQuotasLink,
                       DeleteTenantsAction)
        table_actions = (TenantFilterAction, CreateLink, DeleteTenantsAction)
