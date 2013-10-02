from django import template
from django.template import defaultfilters as filters
from django.utils.translation import ugettext_lazy as _  # noqa

from horizon import tables
from horizon.utils import filters as utils_filters


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
    # if not configured in this region, neither option makes sense
    if service.host:
        return options[0] if not service.disabled else options[1]
    return None


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


def get_available(zone):
    return zone.zoneState['available']


def get_hosts(zone):
    hosts = zone.hosts
    host_details = []
    for name, services in hosts.items():
        up = all([s['active'] and s['available'] for k, s in services.items()])
        up = _("Services Up") if up else _("Services Down")
        host_details.append("%(host)s (%(up)s)" % {'host': name, 'up': up})
    return host_details


class ZonesTable(tables.DataTable):
    name = tables.Column('zoneName', verbose_name=_('Name'))
    hosts = tables.Column(get_hosts,
                          verbose_name=_('Hosts'),
                          wrap_list=True,
                          filters=(filters.unordered_list,))
    available = tables.Column(get_available,
                              verbose_name=_('Available'),
                              status=True,
                              filters=(filters.yesno, filters.capfirst))

    def get_object_id(self, zone):
        return zone.zoneName

    class Meta:
        name = "zones"
        verbose_name = _("Availability Zones")
        multi_select = False
        status_columns = ["available"]


class NovaServiceFilterAction(tables.FilterAction):
    def filter(self, table, services, filter_string):
        q = filter_string.lower()

        def comp(service):
            if q in service.type.lower():
                return True
            return False

        return filter(comp, services)


class NovaServicesTable(tables.DataTable):
    binary = tables.Column("binary", verbose_name=_('Name'))
    host = tables.Column('host', verbose_name=_('Host'))
    zone = tables.Column('zone', verbose_name=_('Zone'))
    status = tables.Column('status', verbose_name=_('Status'))
    state = tables.Column('state', verbose_name=_('State'))
    updated_at = tables.Column('updated_at',
                               verbose_name=_('Updated At'),
                               filters=(utils_filters.parse_isotime,
                                        filters.timesince))

    def get_object_id(self, obj):
        return "%s-%s-%s" % (obj.binary, obj.host, obj.zone)

    class Meta:
        name = "nova_services"
        verbose_name = _("Compute Services")
        table_actions = (NovaServiceFilterAction,)
        multi_select = False


def get_hosts(aggregate):
    return [host for host in aggregate.hosts]


def get_metadata(aggregate):
    return [' = '.join([key, val]) for key, val
            in aggregate.metadata.iteritems()]


class AggregatesTable(tables.DataTable):
    name = tables.Column("name",
                         verbose_name=_("Name"))
    availability_zone = tables.Column("availability_zone",
                                      verbose_name=_("Availability Zone"))
    hosts = tables.Column(get_hosts,
                          verbose_name=_("Hosts"),
                          wrap_list=True,
                          filters=(filters.unordered_list,))
    metadata = tables.Column(get_metadata,
                             verbose_name=_("Metadata"),
                             wrap_list=True,
                             filters=(filters.unordered_list,))

    class Meta:
        name = "aggregates"
        verbose_name = _("Host Aggregates")


class NetworkAgentsFilterAction(tables.FilterAction):
    def filter(self, table, agents, filter_string):
        q = filter_string.lower()

        def comp(agent):
            if q in agent.agent_type.lower():
                return True
            return False

        return filter(comp, agents)


def get_network_agent_status(agent):
    if agent.admin_state_up:
        return _('Enabled')

    return _('Disabled')


def get_network_agent_state(agent):
    if agent.alive:
        return _('Up')

    return _('Down')


class NetworkAgentsTable(tables.DataTable):
    agent_type = tables.Column('agent_type', verbose_name=_('Type'))
    binary = tables.Column("binary", verbose_name=_('Name'))
    host = tables.Column('host', verbose_name=_('Host'))
    status = tables.Column(get_network_agent_status, verbose_name=_('Status'))
    state = tables.Column(get_network_agent_state, verbose_name=_('State'))
    heartbeat_timestamp = tables.Column('heartbeat_timestamp',
                                        verbose_name=_('Updated At'),
                                        filters=(utils_filters.parse_isotime,
                                                 filters.timesince))

    def get_object_id(self, obj):
        return "%s-%s" % (obj.binary, obj.host)

    class Meta:
        name = "network_agents"
        verbose_name = _("Network Agents")
        table_actions = (NetworkAgentsFilterAction,)
        multi_select = False
