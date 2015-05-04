#    Copyright 2013, Big Switch Networks, Inc.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

from __future__ import absolute_import

from django.utils.datastructures import SortedDict
from django.utils.translation import ugettext_lazy as _

from horizon import messages

from openstack_dashboard.api import neutron

neutronclient = neutron.neutronclient


class Vip(neutron.NeutronAPIDictWrapper):
    """Wrapper for neutron load balancer vip."""

    def __init__(self, apiresource):
        super(Vip, self).__init__(apiresource)


class Pool(neutron.NeutronAPIDictWrapper):
    """Wrapper for neutron load balancer pool."""

    def __init__(self, apiresource):
        if 'provider' not in apiresource:
            apiresource['provider'] = None
        super(Pool, self).__init__(apiresource)


class Member(neutron.NeutronAPIDictWrapper):
    """Wrapper for neutron load balancer member."""

    def __init__(self, apiresource):
        super(Member, self).__init__(apiresource)


class PoolStats(neutron.NeutronAPIDictWrapper):
    """Wrapper for neutron load balancer pool stats."""

    def __init__(self, apiresource):
        super(PoolStats, self).__init__(apiresource)


class PoolMonitor(neutron.NeutronAPIDictWrapper):
    """Wrapper for neutron load balancer pool health monitor."""

    def __init__(self, apiresource):
        super(PoolMonitor, self).__init__(apiresource)


def vip_create(request, **kwargs):
    """Create a vip for a specified pool.

    :param request: request context
    :param address: virtual IP address
    :param name: name for vip
    :param description: description for vip
    :param subnet_id: subnet_id for subnet of vip
    :param protocol_port: transport layer port number for vip
    :returns: Vip object
    """
    body = {'vip': {'name': kwargs['name'],
                    'description': kwargs['description'],
                    'subnet_id': kwargs['subnet_id'],
                    'protocol_port': kwargs['protocol_port'],
                    'protocol': kwargs['protocol'],
                    'pool_id': kwargs['pool_id'],
                    'session_persistence': kwargs['session_persistence'],
                    'admin_state_up': kwargs['admin_state_up']
                    }}
    if kwargs.get('connection_limit'):
        body['vip']['connection_limit'] = kwargs['connection_limit']

    if kwargs.get('address'):
        body['vip']['address'] = kwargs['address']

    vip = neutronclient(request).create_vip(body).get('vip')
    return Vip(vip)


def vip_list(request, **kwargs):
    vips = neutronclient(request).list_vips(**kwargs).get('vips')
    return [Vip(v) for v in vips]


def vip_get(request, vip_id):
    return _vip_get(request, vip_id, expand_resource=True)


def _vip_get(request, vip_id, expand_resource=False):
    vip = neutronclient(request).show_vip(vip_id).get('vip')
    if expand_resource:
        vip['subnet'] = neutron.subnet_get(request, vip['subnet_id'])
        vip['port'] = neutron.port_get(request, vip['port_id'])
        vip['pool'] = _pool_get(request, vip['pool_id'])
    return Vip(vip)


def vip_update(request, vip_id, **kwargs):
    vip = neutronclient(request).update_vip(vip_id, kwargs).get('vip')
    return Vip(vip)


def vip_delete(request, vip_id):
    neutronclient(request).delete_vip(vip_id)


def pool_create(request, **kwargs):
    """Create a pool for specified protocol

    :param request: request context
    :param name: name for pool
    :param description: description for pool
    :param subnet_id: subnet_id for subnet of pool
    :param protocol: load balanced protocol
    :param lb_method: load balancer method
    :param admin_state_up: admin state (default on)
    """
    body = {'pool': {'name': kwargs['name'],
                     'description': kwargs['description'],
                     'subnet_id': kwargs['subnet_id'],
                     'protocol': kwargs['protocol'],
                     'lb_method': kwargs['lb_method'],
                     'admin_state_up': kwargs['admin_state_up'],
                     'provider': kwargs['provider'],
                     }}
    pool = neutronclient(request).create_pool(body).get('pool')
    return Pool(pool)


def _get_vip(request, pool, vip_dict, expand_name_only=False):
    if pool['vip_id'] is not None:
        try:
            if vip_dict:
                vip = vip_dict.get(pool['vip_id'])
            else:
                vip = _vip_get(request, pool['vip_id'])
        except Exception:
            messages.warning(request, _("Unable to get VIP for pool "
                                        "%(pool)s.") % {"pool": pool["id"]})
            vip = Vip({'id': pool['vip_id'], 'name': ''})
        if expand_name_only:
            vip = vip.name_or_id
        return vip
    else:
        return None


def pool_list(request, **kwargs):
    return _pool_list(request, expand_subnet=True, expand_vip=True, **kwargs)


def _pool_list(request, expand_subnet=False, expand_vip=False, **kwargs):
    pools = neutronclient(request).list_pools(**kwargs).get('pools')
    if expand_subnet:
        subnets = neutron.subnet_list(request)
        subnet_dict = SortedDict((s.id, s) for s in subnets)
        for p in pools:
            subnet = subnet_dict.get(p['subnet_id'])
            p['subnet_name'] = subnet.cidr if subnet else None
    if expand_vip:
        vips = vip_list(request)
        vip_dict = SortedDict((v.id, v) for v in vips)
        for p in pools:
            p['vip_name'] = _get_vip(request, p, vip_dict,
                                     expand_name_only=True)
    return [Pool(p) for p in pools]


def pool_get(request, pool_id):
    return _pool_get(request, pool_id, expand_resource=True)


def _pool_get(request, pool_id, expand_resource=False):
    try:
        pool = neutronclient(request).show_pool(pool_id).get('pool')
    except Exception:
        messages.warning(request, _("Unable to get pool detail."))
        return None
    if expand_resource:
        # TODO(lyj): The expand resource(subnet, member etc.) attached
        # to a pool could be deleted without cleanup pool related database,
        # this will cause exceptions if we trying to get the deleted resources.
        # so we need to handle the situation by showing a warning message here.
        # we can safely remove the try/except once the neutron bug is fixed
        # https://bugs.launchpad.net/neutron/+bug/1406854
        try:
            pool['subnet'] = neutron.subnet_get(request, pool['subnet_id'])
        except Exception:
            messages.warning(request, _("Unable to get subnet for pool "
                                        "%(pool)s.") % {"pool": pool_id})
        pool['vip'] = _get_vip(request, pool, vip_dict=None,
                               expand_name_only=False)
        try:
            pool['members'] = _member_list(request, expand_pool=False,
                                           pool_id=pool_id)
        except Exception:
            messages.warning(request, _("Unable to get members for pool "
                                        "%(pool)s.") % {"pool": pool_id})
        monitors = []
        for monitor_id in pool['health_monitors']:
            try:
                monitors.append(_pool_health_monitor_get(request, monitor_id,
                                                         False))
            except Exception:
                messages.warning(request,
                                 _("Unable to get health monitor "
                                   "%(monitor_id)s for pool %(pool)s.")
                                 % {"pool": pool_id,
                                    "monitor_id": monitor_id})
        pool['health_monitors'] = monitors
    return Pool(pool)


def pool_update(request, pool_id, **kwargs):
    pool = neutronclient(request).update_pool(pool_id, kwargs).get('pool')
    return Pool(pool)


def pool_delete(request, pool):
    neutronclient(request).delete_pool(pool)


# not linked to UI yet
def pool_stats(request, pool_id, **kwargs):
    stats = neutronclient(request).retrieve_pool_stats(pool_id, **kwargs)
    return PoolStats(stats)


def pool_health_monitor_create(request, **kwargs):
    """Create a health monitor

    :param request: request context
    :param type: type of monitor
    :param delay: delay of monitor
    :param timeout: timeout of monitor
    :param max_retries: max retries [1..10]
    :param http_method: http method
    :param url_path: url path
    :param expected_codes: http return code
    :param admin_state_up: admin state
    """
    monitor_type = kwargs['type'].upper()
    body = {'health_monitor': {'type': monitor_type,
                               'delay': kwargs['delay'],
                               'timeout': kwargs['timeout'],
                               'max_retries': kwargs['max_retries'],
                               'admin_state_up': kwargs['admin_state_up']
                               }}
    if monitor_type in ['HTTP', 'HTTPS']:
        body['health_monitor']['http_method'] = kwargs['http_method']
        body['health_monitor']['url_path'] = kwargs['url_path']
        body['health_monitor']['expected_codes'] = kwargs['expected_codes']
    mon = neutronclient(request).create_health_monitor(body).get(
        'health_monitor')

    return PoolMonitor(mon)


def pool_health_monitor_list(request, **kwargs):
    monitors = neutronclient(request).list_health_monitors(
        **kwargs).get('health_monitors')
    return [PoolMonitor(m) for m in monitors]


def pool_health_monitor_get(request, monitor_id):
    return _pool_health_monitor_get(request, monitor_id, expand_resource=True)


def _pool_health_monitor_get(request, monitor_id, expand_resource=False):
    monitor = neutronclient(request
                            ).show_health_monitor(monitor_id
                                                  ).get('health_monitor')
    if expand_resource:
        pool_ids = [p['pool_id'] for p in monitor['pools']]
        monitor['pools'] = _pool_list(request, id=pool_ids)
    return PoolMonitor(monitor)


def pool_health_monitor_update(request, monitor_id, **kwargs):
    monitor = neutronclient(request
                            ).update_health_monitor(monitor_id, kwargs
                                                    ).get('health_monitor')
    return PoolMonitor(monitor)


def pool_health_monitor_delete(request, mon_id):
    neutronclient(request).delete_health_monitor(mon_id)


def member_create(request, **kwargs):
    """Create a load balance member

    :param request: request context
    :param pool_id: pool_id of pool for member
    :param address: IP address
    :param protocol_port: transport layer port number
    :param weight: weight for member
    :param admin_state_up: admin_state
    """
    body = {'member': {'pool_id': kwargs['pool_id'],
                       'address': kwargs['address'],
                       'protocol_port': kwargs['protocol_port'],
                       'admin_state_up': kwargs['admin_state_up']
                       }}
    if kwargs.get('weight'):
        body['member']['weight'] = kwargs['weight']
    member = neutronclient(request).create_member(body).get('member')
    return Member(member)


def member_list(request, **kwargs):
    return _member_list(request, expand_pool=True, **kwargs)


def _member_list(request, expand_pool, **kwargs):
    members = neutronclient(request).list_members(**kwargs).get('members')
    if expand_pool:
        pools = _pool_list(request)
        pool_dict = SortedDict((p.id, p) for p in pools)
        for m in members:
            m['pool_name'] = pool_dict.get(m['pool_id']).name_or_id
    return [Member(m) for m in members]


def member_get(request, member_id):
    return _member_get(request, member_id, expand_pool=True)


def _member_get(request, member_id, expand_pool):
    member = neutronclient(request).show_member(member_id).get('member')
    if expand_pool:
        member['pool'] = _pool_get(request, member['pool_id'])
    return Member(member)


def member_update(request, member_id, **kwargs):
    member = neutronclient(request).update_member(member_id, kwargs
                                                  ).get('member')
    return Member(member)


def member_delete(request, mem_id):
    neutronclient(request).delete_member(mem_id)


def pool_monitor_association_create(request, **kwargs):
    """Associate a health monitor with pool

    :param request: request context
    :param monitor_id: id of monitor
    :param pool_id: id of pool
    """

    body = {'health_monitor': {'id': kwargs['monitor_id'], }}

    neutronclient(request).associate_health_monitor(
        kwargs['pool_id'], body)


def pool_monitor_association_delete(request, **kwargs):
    """Disassociate a health monitor from pool

    :param request: request context
    :param monitor_id: id of monitor
    :param pool_id: id of pool
    """

    neutronclient(request).disassociate_health_monitor(
        kwargs['pool_id'], kwargs['monitor_id'])
