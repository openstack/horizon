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

from openstack_dashboard.api import neutron

neutronclient = neutron.neutronclient


class Rule(neutron.NeutronAPIDictWrapper):
    """Wrapper for neutron firewall rule"""

    def get_dict(self):
        rule_dict = self._apidict
        rule_dict['rule_id'] = rule_dict['id']
        return rule_dict


class Policy(neutron.NeutronAPIDictWrapper):
    """Wrapper for neutron firewall policy"""

    def get_dict(self):
        policy_dict = self._apidict
        policy_dict['policy_id'] = policy_dict['id']
        return policy_dict


class Firewall(neutron.NeutronAPIDictWrapper):
    """Wrapper for neutron firewall"""

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


def rules_list(request, **kwargs):
    rules = neutronclient(request).list_firewall_rules(
        **kwargs).get('firewall_rules')
    return [Rule(r) for r in rules]


def rule_get(request, rule_id):
    rule = neutronclient(request).show_firewall_rule(
        rule_id).get('firewall_rule')
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


def policies_list(request, **kwargs):
    policies = neutronclient(request).list_firewall_policies(
        **kwargs).get('firewall_policies')
    return [Policy(p) for p in policies]


def policy_get(request, policy_id):
    policy = neutronclient(request).show_firewall_policy(
        policy_id).get('firewall_policy')
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


def firewalls_list(request, **kwargs):
    firewalls = neutronclient(request).list_firewalls(
        **kwargs).get('firewalls')
    return [Firewall(f) for f in firewalls]


def firewall_get(request, firewall_id):
    firewall = neutronclient(request).show_firewall(
        firewall_id).get('firewall')
    return Firewall(firewall)


def firewall_delete(request, firewall_id):
    neutronclient(request).delete_firewall(firewall_id)


def firewall_update(request, firewall_id, **kwargs):
    body = {'firewall': kwargs}
    firewall = neutronclient(request).update_firewall(
        firewall_id, body).get('firewall')
    return Firewall(firewall)
