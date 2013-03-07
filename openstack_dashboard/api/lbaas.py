# vim: tabstop=4 shiftwidth=4 softtabstop=4

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

from openstack_dashboard.api.quantum import QuantumAPIDictWrapper
from openstack_dashboard.api.quantum import quantumclient
from openstack_dashboard.api.quantum import subnet_get


class Vip(QuantumAPIDictWrapper):
    """Wrapper for quantum load balancer vip"""

    def __init__(self, apiresource):
        super(Vip, self).__init__(apiresource)


class Pool(QuantumAPIDictWrapper):
    """Wrapper for quantum load balancer pool"""

    def __init__(self, apiresource):
        super(Pool, self).__init__(apiresource)

    class AttributeDict(dict):
        def __getattr__(self, attr):
            return self[attr]

        def __setattr__(self, attr, value):
            self[attr] = value

    def readable(self, request):
        pFormatted = {'id': self.id,
                      'name': self.name,
                      'description': self.description,
                      'protocol': self.protocol}
        try:
            pFormatted['subnet_id'] = self.subnet_id
            pFormatted['subnet_name'] = subnet_get(
                request, self.subnet_id).cidr
        except:
            pFormatted['subnet_id'] = self.subnet_id
            pFormatted['subnet_name'] = self.subnet_id

        if self.vip_id is not None:
            try:
                pFormatted['vip_id'] = self.vip_id
                pFormatted['vip_name'] = vip_get(
                    request, self.vip_id).name
            except:
                pFormatted['vip_id'] = self.vip_id
                pFormatted['vip_name'] = self.vip_id
        else:
            pFormatted['vip_id'] = None
            pFormatted['vip_name'] = None

        return self.AttributeDict(pFormatted)


class Member(QuantumAPIDictWrapper):
    """Wrapper for quantum load balancer member"""

    def __init__(self, apiresource):
        super(Member, self).__init__(apiresource)

    class AttributeDict(dict):
        def __getattr__(self, attr):
            return self[attr]

        def __setattr__(self, attr, value):
            self[attr] = value

    def readable(self, request):
        mFormatted = {'id': self.id,
                      'address': self.address,
                      'protocol_port': self.protocol_port}
        try:
            mFormatted['pool_id'] = self.pool_id
            mFormatted['pool_name'] = pool_get(
                request, self.pool_id).name
        except:
            mFormatted['pool_id'] = self.pool_id
            mFormatted['pool_name'] = self.pool_id

        return self.AttributeDict(mFormatted)


class PoolStats(QuantumAPIDictWrapper):
    """Wrapper for quantum load balancer pool stats"""

    def __init__(self, apiresource):
        super(PoolStats, self).__init__(apiresource)


class PoolMonitor(QuantumAPIDictWrapper):
    """Wrapper for quantum load balancer pool health monitor"""

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
    body = {'vip': {'address': kwargs['address'],
                    'name': kwargs['name'],
                    'description': kwargs['description'],
                    'subnet_id': kwargs['subnet_id'],
                    'protocol_port': kwargs['protocol_port'],
                    'protocol': kwargs['protocol'],
                    'pool_id': kwargs['pool_id'],
                    'session_persistence': kwargs['session_persistence'],
                    'connection_limit': kwargs['connection_limit'],
                    'admin_state_up': kwargs['admin_state_up']
                    }}
    vip = quantumclient(request).create_vip(body).get('vip')
    return Vip(vip)


def vips_get(request, **kwargs):
    vips = quantumclient(request).list_vips().get('vips')
    return [Vip(v) for v in vips]


def vip_get(request, vip_id):
    vip = quantumclient(request).show_vip(vip_id).get('vip')
    return Vip(vip)


# not linked to UI yet
def vip_update(request, vip_id, **kwargs):
    vip = quantumclient(request).update_vip(vip_id, kwargs).get('vip')
    return Vip(vip)


def vip_delete(request, vip_id):
    quantumclient(request).delete_vip(vip_id)


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
                     'admin_state_up': kwargs['admin_state_up']
                     }}
    pool = quantumclient(request).create_pool(body).get('pool')
    return Pool(pool)


def pools_get(request, **kwargs):
    pools = quantumclient(request).list_pools().get('pools')
    return [Pool(p) for p in pools]


def pool_get(request, pool_id):
    pool = quantumclient(request).show_pool(pool_id).get('pool')
    return Pool(pool)


def pool_update(request, pool_id, **kwargs):
    pool = quantumclient(request).update_pool(pool_id, kwargs).get('pool')
    return Pool(pool)


def pool_delete(request, pool):
    quantumclient(request).delete_pool(pool)


# not linked to UI yet
def pool_stats(request, pool_id, **kwargs):
    stats = quantumclient(request).retrieve_pool_stats(pool_id, **kwargs)
    return PoolStats(stats)


def pool_health_monitor_create(request, **kwargs):
    """Create a health monitor and associate with pool

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
    mon = quantumclient(request).create_health_monitor(body).get(
        'health_monitor')
    body = {'health_monitor': {'id': mon['id']}}
    quantumclient(request).associate_health_monitor(
        kwargs['pool_id'], body)
    return PoolMonitor(mon)


def pool_health_monitors_get(request, **kwargs):
    monitors = quantumclient(request
                             ).list_health_monitors().get('health_monitors')
    return [PoolMonitor(m) for m in monitors]


def pool_health_monitor_get(request, monitor_id):
    monitor = quantumclient(request
                            ).show_health_monitor(monitor_id
                                                  ).get('health_monitor')
    return PoolMonitor(monitor)


def pool_health_monitor_delete(request, mon_id):
    quantumclient(request).delete_health_monitor(mon_id)


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
                       'weight': kwargs['weight'],
                       'admin_state_up': kwargs['admin_state_up']
                       }}
    member = quantumclient(request).create_member(body).get('member')
    return Member(member)


def members_get(request, **kwargs):
    members = quantumclient(request).list_members().get('members')
    return [Member(m) for m in members]


def member_get(request, member_id):
    member = quantumclient(request).show_member(member_id).get('member')
    return Member(member)


# not linked to UI yet
def member_update(request, member_id, **kwargs):
    member = quantumclient(request).update_member(member_id, kwargs)
    return Member(member)


def member_delete(request, mem_id):
    quantumclient(request).delete_member(mem_id)
