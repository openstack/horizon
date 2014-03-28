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

from django import template
from django.template import defaultfilters as filters
from django.utils.translation import ugettext_lazy as _

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
    id = tables.Column('id', hidden=True)
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


class QuotaFilterAction(tables.FilterAction):
    def filter(self, table, tenants, filter_string):
        q = filter_string.lower()

        def comp(tenant):
            if q in tenant.name.lower():
                return True
            return False

        return filter(comp, tenants)


def get_quota_name(quota):
    QUOTA_NAMES = {
        'injected_file_content_bytes': _('Injected File Content Bytes'),
        'injected_file_path_bytes': _('Injected File Path Bytes'),
        'metadata_items': _('Metadata Items'),
        'cores': _('VCPUs'),
        'instances': _('Instances'),
        'injected_files': _('Injected Files'),
        'volumes': _('Volumes'),
        'snapshots': _('Volume Snapshots'),
        'gigabytes': _('Total Size of Volumes and Snapshots (GB)'),
        'ram': _('RAM (MB)'),
        'floating_ips': _('Floating IPs'),
        'security_groups': _('Security Groups'),
        'security_group_rules': _('Security Group Rules'),
        'key_pairs': _('Key Pairs'),
        'fixed_ips': _('Fixed IPs'),
        'volumes_volume_luks': _('LUKS Volumes'),
        'snapshots_volume_luks': _('LUKS Volume Snapshots'),
        'gigabytes_volume_luks':
        _('Total Size of LUKS Volumes and Snapshots (GB)'),
        'dm-crypt': _('dm-crypt'),
    }
    return QUOTA_NAMES.get(quota.name, quota.name.replace("_", " ").title())


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
