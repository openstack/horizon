import logging

from django import template
from django.utils.translation import ugettext_lazy as _

from horizon import tables
from horizon import api


LOG = logging.getLogger(__name__)


class ServiceFilterAction(tables.FilterAction):
    def filter(self, table, services, filter_string):
        q = filter_string.lower()

        def comp(service):
            if q in service.type.lower():
                return True
            return False

        return filter(comp, services)


def get_stats(service):
    return template.loader.render_to_string('syspanel/services/_stats.html',
                                            {'service': service})


def get_enabled(service, reverse=False):
    options = ["Enabled", "Disabled"]
    if reverse:
        options.reverse()
    return options[0] if not service.disabled else options[1]


def get_service_name(service):
    if(service.type == "identity"):
        return _("%(type)s (%(backend)s backend)") \
                 % {"type": service.type,
                    "backend": api.keystone_backend_name()}
    else:
        return service.type


class ServicesTable(tables.DataTable):
    id = tables.Column('id', verbose_name=_('Id'), hidden=True)
    service = tables.Column(get_service_name, verbose_name=_('Service'))
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
