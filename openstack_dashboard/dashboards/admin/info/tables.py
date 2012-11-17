import logging

from django.utils.translation import ugettext_lazy as _

from horizon import tables


LOG = logging.getLogger(__name__)


class QuotaFilterAction(tables.FilterAction):
    def filter(self, table, tenants, filter_string):
        q = filter_string.lower()

        def comp(tenant):
            if q in tenant.name.lower():
                return True
            return False

        return filter(comp, tenants)


def get_quota_name(quota):
    return quota.name.replace("_", " ").title()


class QuotasTable(tables.DataTable):
    name = tables.Column(get_quota_name, verbose_name=_('Quota Name'))
    limit = tables.Column("limit", verbose_name=_('Limit'))

    def get_object_id(self, obj):
        return obj.name

    class Meta:
        name = "quotas"
        verbose_name = _("Quotas")
        table_actions = (QuotaFilterAction,)
        multi_select = False


class ServiceFilterAction(tables.FilterAction):
    def filter(self, table, services, filter_string):
        q = filter_string.lower()

        def comp(service):
            if q in service.type.lower():
                return True
            return False

        return filter(comp, services)


def get_stats(service):
    return template.loader.render_to_string('admin/services/_stats.html',
                                            {'service': service})


def get_enabled(service, reverse=False):
    options = ["Enabled", "Disabled"]
    if reverse:
        options.reverse()
    return options[0] if not service.disabled else options[1]


class ServicesTable(tables.DataTable):
    id = tables.Column('id', verbose_name=_('Id'), hidden=True)
    name = tables.Column("name", verbose_name=_('Name'))
    service_type = tables.Column('__unicode__', verbose_name=_('Service'))
    host = tables.Column('host', verbose_name=_('Host'))
    enabled = tables.Column(get_enabled,
                            verbose_name=_('Enabled'),
                            status=True)

    class Meta:
        name = "services"
        verbose_name = _("Services")
        table_actions = (ServiceFilterAction,)
        multi_select = False
        status_columns = ["enabled"]
