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

from horizon.utils import memoized

from openstack_dashboard.api import neutron

neutronclient = neutron.neutronclient


class Rule(neutron.NeutronAPIDictWrapper):
    """Wrapper for neutron firewall rule."""

    def get_dict(self):
        rule_dict = self._apidict
        rule_dict['rule_id'] = rule_dict['id']
        return rule_dict


class Policy(neutron.NeutronAPIDictWrapper):
    """Wrapper for neutron firewall policy."""

    def get_dict(self):
        policy_dict = self._apidict
        policy_dict['policy_id'] = policy_dict['id']
        return policy_dict


class Firewall(neutron.NeutronAPIDictWrapper):
    """Wrapper for neutron firewall."""

    def __init__(self, apiresource):
        apiresource['admin_state'] = \
            'UP' if apiresource['admin_state_up'] else 'DOWN'
        super(Firewall, self).__init__(apiresource)

    def get_dict(self):
        firewall_dict = self._apidict
        firewall_dict['firewall_id'] = firewall_dict['id']
        return firewall_dict


def rule_create(request, **kwargs):
    """Create a firewall rule

    :param request: request context
    :param name: name for rule
    :param description: description for rule
    :param protocol: protocol for rule
    :param action: action for rule
    :param source_ip_address: source IP address or subnet
    :param source_port: integer in [1, 65535] or range in a:b
    :param destination_ip_address: destination IP address or subnet
    :param destination_port: integer in [1, 65535] or range in a:b
    :param shared: boolean (default false)
    :param enabled: boolean (default true)
    :return: Rule object
    """
    body = {'firewall_rule': kwargs}
    rule = neutronclient(request).create_firewall_rule(
        body).get('firewall_rule')
    return Rule(rule)


def rule_list(request, **kwargs):
    return _rule_list(request, expand_policy=True, **kwargs)


def rule_list_for_tenant(request, tenant_id, **kwargs):
    """Return a rule list available for the tenant.

    The list contains rules owned by the tenant and shared rules.
    This is required because Neutron returns all resources including
    all tenants if a user has admin role.
    """
    rules = rule_list(request, tenant_id=tenant_id, shared=False, **kwargs)
    shared_rules = rule_list(request, shared=True, **kwargs)
    return rules + shared_rules


def _rule_list(request, expand_policy, **kwargs):
    rules = neutronclient(request).list_firewall_rules(
        **kwargs).get('firewall_rules')
    if expand_policy and rules:
        policies = _policy_list(request, expand_rule=False)
        policy_dict = SortedDict((p.id, p) for p in policies)
        for rule in rules:
            rule['policy'] = policy_dict.get(rule['firewall_policy_id'])
    return [Rule(r) for r in rules]


def rule_get(request, rule_id):
    return _rule_get(request, rule_id, expand_policy=True)


def _rule_get(request, rule_id, expand_policy):
    rule = neutronclient(request).show_firewall_rule(
        rule_id).get('firewall_rule')
    if expand_policy:
        if rule['firewall_policy_id']:
            rule['policy'] = _policy_get(request, rule['firewall_policy_id'],
                                         expand_rule=False)
        else:
            rule['policy'] = None
    return Rule(rule)


def rule_delete(request, rule_id):
    neutronclient(request).delete_firewall_rule(rule_id)


def rule_update(request, rule_id, **kwargs):
    body = {'firewall_rule': kwargs}
    rule = neutronclient(request).update_firewall_rule(
        rule_id, body).get('firewall_rule')
    return Rule(rule)


def policy_create(request, **kwargs):
    """Create a firewall policy

    :param request: request context
    :param name: name for policy
    :param description: description for policy
    :param firewall_rules: ordered list of rules in policy
    :param shared: boolean (default false)
    :param audited: boolean (default false)
    :return: Policy object
    """
    body = {'firewall_policy': kwargs}
    policy = neutronclient(request).create_firewall_policy(
        body).get('firewall_policy')
    return Policy(policy)


def policy_list(request, **kwargs):
    return _policy_list(request, expand_rule=True, **kwargs)


def policy_list_for_tenant(request, tenant_id, **kwargs):
    """Return a policy list available for the tenant.

    The list contains policies owned by the tenant and shared policies.
    This is required because Neutron returns all resources including
    all tenants if a user has admin role.
    """
    policies = policy_list(request, tenant_id=tenant_id,
                           shared=False, **kwargs)
    shared_policies = policy_list(request, shared=True, **kwargs)
    return policies + shared_policies


def _policy_list(request, expand_rule, **kwargs):
    policies = neutronclient(request).list_firewall_policies(
        **kwargs).get('firewall_policies')
    if expand_rule and policies:
        rules = _rule_list(request, expand_policy=False)
        rule_dict = SortedDict((rule.id, rule) for rule in rules)
        for p in policies:
            p['rules'] = [rule_dict.get(rule) for rule in p['firewall_rules']]
    return [Policy(p) for p in policies]


def policy_get(request, policy_id):
    return _policy_get(request, policy_id, expand_rule=True)


def _policy_get(request, policy_id, expand_rule):
    policy = neutronclient(request).show_firewall_policy(
        policy_id).get('firewall_policy')
    if expand_rule:
        policy_rules = policy['firewall_rules']
        if policy_rules:
            rules = _rule_list(request, expand_policy=False,
                               firewall_policy_id=policy_id)
            rule_dict = SortedDict((rule.id, rule) for rule in rules)
            policy['rules'] = [rule_dict.get(rule) for rule in policy_rules]
        else:
            policy['rules'] = []
    return Policy(policy)


def policy_delete(request, policy_id):
    neutronclient(request).delete_firewall_policy(policy_id)


def policy_update(request, policy_id, **kwargs):
    body = {'firewall_policy': kwargs}
    policy = neutronclient(request).update_firewall_policy(
        policy_id, body).get('firewall_policy')
    return Policy(policy)


def policy_insert_rule(request, policy_id, **kwargs):
    policy = neutronclient(request).firewall_policy_insert_rule(
        policy_id, kwargs)
    return Policy(policy)


def policy_remove_rule(request, policy_id, **kwargs):
    policy = neutronclient(request).firewall_policy_remove_rule(
        policy_id, kwargs)
    return Policy(policy)


def firewall_create(request, **kwargs):
    """Create a firewall for specified policy

    :param request: request context
    :param name: name for firewall
    :param description: description for firewall
    :param firewall_policy_id: policy id used by firewall
    :param shared: boolean (default false)
    :param admin_state_up: boolean (default true)
    :return: Firewall object
    """
    body = {'firewall': kwargs}
    firewall = neutronclient(request).create_firewall(body).get('firewall')
    return Firewall(firewall)


def firewall_list(request, **kwargs):
    return _firewall_list(request, expand_policy=True, **kwargs)


def firewall_list_for_tenant(request, tenant_id, **kwargs):
    """Return a firewall list available for the tenant.

    The list contains firewalls owned by the tenant and shared firewalls.
    This is required because Neutron returns all resources including
    all tenants if a user has admin role.
    """
    # NOTE(amotoki): At now 'shared' attribute is not visible in Neutron
    # and there is no way to query shared firewalls explicitly.
    # Thus this method returns the same as when tenant_id is specified,
    # but I would like to have this method for symmetry to firewall
    # rules and policies to avoid unnecessary confusion.
    return firewall_list(request, tenant_id=tenant_id, **kwargs)


def _firewall_list(request, expand_policy, **kwargs):
    firewalls = neutronclient(request).list_firewalls(
        **kwargs).get('firewalls')
    if expand_policy and firewalls:
        policies = _policy_list(request, expand_rule=False)
        policy_dict = SortedDict((p.id, p) for p in policies)
        for fw in firewalls:
            fw['policy'] = policy_dict.get(fw['firewall_policy_id'])
    return [Firewall(f) for f in firewalls]


def firewall_get(request, firewall_id):
    return _firewall_get(request, firewall_id, expand_policy=True)


def _firewall_get(request, firewall_id, expand_policy):
    firewall = neutronclient(request).show_firewall(
        firewall_id).get('firewall')
    if expand_policy:
        policy_id = firewall['firewall_policy_id']
        if policy_id:
            firewall['policy'] = _policy_get(request, policy_id,
                                             expand_rule=False)
        else:
            firewall['policy'] = None
    return Firewall(firewall)


def firewall_delete(request, firewall_id):
    neutronclient(request).delete_firewall(firewall_id)


def firewall_update(request, firewall_id, **kwargs):
    body = {'firewall': kwargs}
    firewall = neutronclient(request).update_firewall(
        firewall_id, body).get('firewall')
    return Firewall(firewall)


@memoized.memoized
def firewall_unassociated_routers_list(request, tenant_id):
    all_routers = neutron.router_list(request, tenant_id=tenant_id)
    tenant_firewalls = firewall_list_for_tenant(request, tenant_id=tenant_id)
    firewall_router_ids = [rid
                           for fw in tenant_firewalls
                           for rid in getattr(fw, 'router_ids', [])]

    available_routers = [r for r in all_routers
                         if r.id not in firewall_router_ids]
    available_routers = sorted(available_routers,
                               key=lambda router: router.name_or_id)
    return available_routers
