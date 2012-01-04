import logging

from django import shortcuts
from django import template
from django.contrib import messages
from django.utils.translation import ugettext_lazy as _

from horizon import api
from horizon import tables


LOG = logging.getLogger(__name__)


class ToggleServiceAction(tables.Action):
    name = "toggle"

    def allowed(self, request, service):
        return service.id is not None

    def update(self, request, service):
        if not service.disabled:
            self.verbose_name = _("Disable")
        else:
            self.verbose_name = _("Enable")

    def single(self, data_table, request, obj_id):
        service = self.table.get_object_by_id(int(obj_id))
        verb = get_enabled(service, reverse=True).lower()
        try:
            api.service_update(request, obj_id, not service.disabled)
            messages.info(request,
                          _("Service '%(service)s' has been %(verb)s.")
                            % {'service': service.type, "verb": verb})
        except Exception, e:
            LOG.exception('Exception while toggling service %s' % obj_id)
            messages.error(request,
                           _("Unable to update service '%(id)s': %(msg)s")
                           % {"id": obj_id, "msg": e})
        return shortcuts.redirect('horizon:syspanel:services:index')


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


class ServicesTable(tables.DataTable):
    id = tables.Column('id', verbose_name=_('Id'), hidden=True)
    service = tables.Column('type', verbose_name=_('Service'))
    host = tables.Column('host', verbose_name=_('Host'))
    stats = tables.Column(get_stats, verbose_name=_('System Stats'))
    enabled = tables.Column(get_enabled,
                            verbose_name=_('Enabled'),
                            status=True)

    class Meta:
        name = "services"
        verbose_name = _("Services")
        table_actions = (ServiceFilterAction,)
        row_actions = (ToggleServiceAction,)
        multi_select = False
        status_column = "enabled"
