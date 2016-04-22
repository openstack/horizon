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

from django.core import urlresolvers
from django import template
from django.template import defaultfilters as filters
from django.utils.translation import pgettext_lazy
from django.utils.translation import ugettext_lazy as _

from horizon import tables
from horizon.utils import filters as utils_filters


SERVICE_ENABLED = "enabled"
SERVICE_DISABLED = "disabled"

SERVICE_STATUS_DISPLAY_CHOICES = (
    (SERVICE_ENABLED, _("Enabled")),
    (SERVICE_DISABLED, _("Disabled")),
)

SERVICE_STATE_DISPLAY_CHOICES = (
    ('up', _("Up")),
    ('down', _("Down")),
)


class ServiceFilterAction(tables.FilterAction):
    filter_field = 'type'

    def filter(self, table, services, filter_string):
        q = filter_string.lower()

        def comp(service):
            attr = getattr(service, self.filter_field, '')
            if attr is not None and q in attr.lower():
                return True
            return False

        return filter(comp, services)


class SubServiceFilterAction(ServiceFilterAction):
    filter_field = 'binary'


def get_status(service):
    # if not configured in this region, neither option makes sense
    if service.host:
        return SERVICE_ENABLED if not service.disabled else SERVICE_DISABLED
    return None


class ServicesTable(tables.DataTable):
    id = tables.Column('id', hidden=True)
    name = tables.Column("name", verbose_name=_('Name'))
    service_type = tables.Column('__unicode__', verbose_name=_('Service'))
    host = tables.Column('host', verbose_name=_('Host'))
    status = tables.Column(get_status,
                           verbose_name=_('Status'),
                           status=True,
                           display_choices=SERVICE_STATUS_DISPLAY_CHOICES)

    class Meta(object):
        name = "services"
        verbose_name = _("Services")
        table_actions = (ServiceFilterAction,)
        multi_select = False
        status_columns = ["status"]


def get_available(zone):
    return zone.zoneState['available']


def get_agent_status(agent):
    template_name = 'admin/info/_cell_status.html'
    context = {
        'status': agent.status,
        'disabled_reason': agent.disabled_reason
    }
    return template.loader.render_to_string(template_name, context)


class NovaServicesTable(tables.DataTable):
    binary = tables.Column("binary", verbose_name=_('Name'))
    host = tables.Column('host', verbose_name=_('Host'))
    zone = tables.Column('zone', verbose_name=_('Zone'))
    status = tables.Column(get_agent_status, verbose_name=_('Status'))
    state = tables.Column('state', verbose_name=_('State'),
                          display_choices=SERVICE_STATE_DISPLAY_CHOICES)
    updated_at = tables.Column('updated_at',
                               verbose_name=pgettext_lazy(
                                   'Time since the last update',
                                   u'Last Updated'),
                               filters=(utils_filters.parse_isotime,
                                        filters.timesince))

    def get_object_id(self, obj):
        return "%s-%s-%s" % (obj.binary, obj.host, obj.zone)

    class Meta(object):
        name = "nova_services"
        verbose_name = _("Compute Services")
        table_actions = (SubServiceFilterAction,)
        multi_select = False


class CinderServicesTable(tables.DataTable):
    binary = tables.Column("binary", verbose_name=_('Name'))
    host = tables.Column('host', verbose_name=_('Host'))
    zone = tables.Column('zone', verbose_name=_('Zone'))
    status = tables.Column(get_agent_status, verbose_name=_('Status'))
    state = tables.Column('state', verbose_name=_('State'),
                          display_choices=SERVICE_STATE_DISPLAY_CHOICES)
    updated_at = tables.Column('updated_at',
                               verbose_name=pgettext_lazy(
                                   'Time since the last update',
                                   u'Last Updated'),
                               filters=(utils_filters.parse_isotime,
                                        filters.timesince))

    def get_object_id(self, obj):
        return "%s-%s-%s" % (obj.binary, obj.host, obj.zone)

    class Meta(object):
        name = "cinder_services"
        verbose_name = _("Block Storage Services")
        table_actions = (SubServiceFilterAction,)
        multi_select = False


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


class NetworkL3AgentRoutersLinkAction(tables.LinkAction):
    name = "l3_agent_router_link"
    verbose_name = _("View Routers")

    def allowed(self, request, datum):
        # Determine whether this action is allowed for the current request.
        return datum.agent_type == "L3 agent"

    def get_link_url(self, datum=None):
        obj_id = datum.id
        return urlresolvers.reverse("horizon:admin:routers:l3_agent_list",
                                    args=(obj_id,))


class NetworkAgentsTable(tables.DataTable):
    agent_type = tables.Column('agent_type', verbose_name=_('Type'))
    binary = tables.Column("binary", verbose_name=_('Name'))
    host = tables.Column('host', verbose_name=_('Host'))
    status = tables.Column(get_network_agent_status, verbose_name=_('Status'))
    state = tables.Column(get_network_agent_state, verbose_name=_('State'))
    heartbeat_timestamp = tables.Column('heartbeat_timestamp',
                                        verbose_name=pgettext_lazy(
                                            'Time since the last update',
                                            u'Last Updated'),
                                        filters=(utils_filters.parse_isotime,
                                                 filters.timesince))

    def get_object_id(self, obj):
        return "%s-%s" % (obj.binary, obj.host)

    class Meta(object):
        name = "network_agents"
        verbose_name = _("Network Agents")
        table_actions = (NetworkAgentsFilterAction, )
        row_actions = (NetworkL3AgentRoutersLinkAction, )
        multi_select = False


class HeatServiceFilterAction(tables.FilterAction):
    filter_field = 'type'

    def filter(self, table, services, filter_string):
        q = filter_string.lower()

        def comp(service):
            attr = getattr(service, self.filter_field, '')
            if attr is not None and q in attr.lower():
                return True
            return False

        return filter(comp, services)


class HeatServiceTable(tables.DataTable):
    hostname = tables.Column('hostname', verbose_name=_('Hostname'))
    binary = tables.Column("binary", verbose_name=_('Name'))
    engine_id = tables.Column('engine_id', verbose_name=_('Engine Id'))
    host = tables.Column('host', verbose_name=_('Host'))
    topic = tables.Column('topic', verbose_name=_('Topic'))
    # For consistent with other tables in system info, set column name to
    # 'state'
    state = tables.Column('status', verbose_name=_('State'),
                          display_choices=SERVICE_STATE_DISPLAY_CHOICES)
    updated_at = tables.Column('updated_at',
                               verbose_name=pgettext_lazy(
                                   'Time since the last update',
                                   u'Last Updated'),
                               filters=(utils_filters.parse_isotime,
                                        filters.timesince))

    def get_object_id(self, obj):
        return "%s" % obj.engine_id

    class Meta(object):
        name = "heat_services"
        verbose_name = _("Orchestration Services")
        table_actions = (HeatServiceFilterAction,)
        multi_select = False
