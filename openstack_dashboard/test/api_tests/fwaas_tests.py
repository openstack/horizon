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
#
# @author: KC Wang, Big Switch Networks
#

from openstack_dashboard import api
from openstack_dashboard.test import helpers as test

from neutronclient.v2_0.client import Client as neutronclient  # noqa


class FwaasApiTests(test.APITestCase):
    @test.create_stubs({neutronclient: ('create_firewall_rule',)})
    def test_rule_create(self):
        rule1 = self.fw_rules.first()
        rule1_dict = self.api_fw_rules.first()
        form_data = {'name': rule1.name,
                     'description': rule1.description,
                     'protocol': rule1.protocol,
                     'action': rule1.action,
                     'source_ip_address': rule1.source_ip_address,
                     'source_port': rule1.source_port,
                     'destination_ip_address': rule1.destination_ip_address,
                     'destination_port': rule1.destination_port,
                     'shared': rule1.shared,
                     'enabled': rule1.enabled
                     }
        form_dict = {'firewall_rule': form_data}
        ret_dict = {'firewall_rule': rule1_dict}
        neutronclient.create_firewall_rule(form_dict).AndReturn(ret_dict)
        self.mox.ReplayAll()

        ret_val = api.fwaas.rule_create(self.request, **form_data)
        self.assertIsInstance(ret_val, api.fwaas.Rule)
        self.assertEqual(rule1.name, ret_val.name)
        self.assertTrue(ret_val.id)

    @test.create_stubs({neutronclient: ('list_firewall_rules',
                                        'list_firewall_policies')})
    def test_rule_list(self):
        exp_rules = self.fw_rules.list()
        api_rules = {'firewall_rules': self.api_fw_rules.list()}
        api_policies = {'firewall_policies': self.api_fw_policies.list()}

        neutronclient.list_firewall_rules().AndReturn(api_rules)
        neutronclient.list_firewall_policies().AndReturn(api_policies)
        self.mox.ReplayAll()

        ret_val = api.fwaas.rule_list(self.request)
        for (v, d) in zip(ret_val, exp_rules):
            self.assertIsInstance(v, api.fwaas.Rule)
            self.assertEqual(v.name, d.name)
            self.assertTrue(v.id)
            if d.policy:
                self.assertEqual(v.policy.id, d.firewall_policy_id)
                self.assertEqual(v.policy.name, d.policy.name)
            else:
                self.assertIsNone(v.policy)

    @test.create_stubs({neutronclient: ('show_firewall_rule',
                                        'show_firewall_policy')})
    def test_rule_get(self):
        exp_rule = self.fw_rules.first()
        ret_dict = {'firewall_rule': self.api_fw_rules.first()}
        policy_dict = {'firewall_policy': self.api_fw_policies.first()}

        neutronclient.show_firewall_rule(exp_rule.id).AndReturn(ret_dict)
        neutronclient.show_firewall_policy(
            exp_rule.firewall_policy_id).AndReturn(policy_dict)
        self.mox.ReplayAll()

        ret_val = api.fwaas.rule_get(self.request, exp_rule.id)
        self.assertIsInstance(ret_val, api.fwaas.Rule)
        self.assertEqual(exp_rule.name, ret_val.name)
        self.assertTrue(ret_val.id)
        self.assertEqual(ret_val.policy.id, exp_rule.firewall_policy_id)
        self.assertEqual(ret_val.policy.name, exp_rule.policy.name)

    @test.create_stubs({neutronclient: ('update_firewall_rule',)})
    def test_rule_update(self):
        rule = self.fw_rules.first()
        rule_dict = self.api_fw_rules.first()

        rule.name = 'new name'
        rule.description = 'new desc'
        rule.protocol = 'icmp'
        rule.action = 'deny'
        rule.shared = True
        rule.enabled = False

        rule_dict['name'] = 'new name'
        rule_dict['description'] = 'new desc'
        rule_dict['protocol'] = 'icmp'
        rule_dict['action'] = 'deny'
        rule_dict['shared'] = True
        rule_dict['enabled'] = False

        form_data = {'name': rule.name,
                     'description': rule.description,
                     'protocol': rule.protocol,
                     'action': rule.action,
                     'shared': rule.shared,
                     'enabled': rule.enabled
                     }
        form_dict = {'firewall_rule': form_data}
        ret_dict = {'firewall_rule': rule_dict}

        neutronclient.update_firewall_rule(
            rule.id, form_dict).AndReturn(ret_dict)
        self.mox.ReplayAll()

        ret_val = api.fwaas.rule_update(self.request,
                                        rule.id, **form_data)
        self.assertIsInstance(ret_val, api.fwaas.Rule)
        self.assertEqual(rule.name, ret_val.name)
        self.assertTrue(ret_val.id)

    @test.create_stubs({neutronclient: ('create_firewall_policy', )})
    def test_policy_create(self):
        policy1 = self.fw_policies.first()
        policy1_dict = self.api_fw_policies.first()

        form_data = {'name': policy1.name,
                     'description': policy1.description,
                     'firewall_rules': policy1.firewall_rules,
                     'shared': policy1.shared,
                     'audited': policy1.audited
                     }
        form_dict = {'firewall_policy': form_data}
        ret_dict = {'firewall_policy': policy1_dict}

        neutronclient.create_firewall_policy(form_dict).AndReturn(ret_dict)
        self.mox.ReplayAll()

        ret_val = api.fwaas.policy_create(self.request, **form_data)
        self.assertIsInstance(ret_val, api.fwaas.Policy)
        self.assertEqual(policy1.name, ret_val.name)
        self.assertTrue(ret_val.id)

    @test.create_stubs({neutronclient: ('list_firewall_policies',
                                        'list_firewall_rules')})
    def test_policy_list(self):
        exp_policies = self.fw_policies.list()
        policies_dict = {'firewall_policies': self.api_fw_policies.list()}
        rules_dict = {'firewall_rules': self.api_fw_rules.list()}

        neutronclient.list_firewall_policies().AndReturn(policies_dict)
        neutronclient.list_firewall_rules().AndReturn(rules_dict)
        self.mox.ReplayAll()

        ret_val = api.fwaas.policy_list(self.request)
        for (v, d) in zip(ret_val, exp_policies):
            self.assertIsInstance(v, api.fwaas.Policy)
            self.assertEqual(v.name, d.name)
            self.assertTrue(v.id)
            self.assertEqual(len(d.firewall_rules), len(v.rules))
            self.assertEqual(len(d.firewall_rules), len(v.firewall_rules))
            for (r, exp_r) in zip(v.rules, d.rules):
                self.assertEqual(r.id, exp_r.id)

    @test.create_stubs({neutronclient: ('show_firewall_policy',
                                        'list_firewall_rules')})
    def test_policy_get(self):
        exp_policy = self.fw_policies.first()
        policy_dict = self.api_fw_policies.first()
        # The first two rules are associated with the first policy.
        api_rules = self.api_fw_rules.list()[:2]

        ret_dict = {'firewall_policy': policy_dict}
        neutronclient.show_firewall_policy(exp_policy.id).AndReturn(ret_dict)
        filters = {'firewall_policy_id': exp_policy.id}
        ret_dict = {'firewall_rules': api_rules}
        neutronclient.list_firewall_rules(**filters).AndReturn(ret_dict)
        self.mox.ReplayAll()

        ret_val = api.fwaas.policy_get(self.request, exp_policy.id)
        self.assertIsInstance(ret_val, api.fwaas.Policy)
        self.assertEqual(exp_policy.name, ret_val.name)
        self.assertTrue(ret_val.id)
        self.assertEqual(len(exp_policy.rules), len(ret_val.rules))
        for (exp, ret) in zip(exp_policy.rules, ret_val.rules):
            self.assertEqual(exp.id, ret.id)

    @test.create_stubs({neutronclient: ('show_firewall_policy',)})
    def test_policy_get_no_rule(self):
        # 2nd policy is not associated with any rules.
        exp_policy = self.fw_policies.list()[1]
        policy_dict = self.api_fw_policies.list()[1]

        ret_dict = {'firewall_policy': policy_dict}
        neutronclient.show_firewall_policy(exp_policy.id).AndReturn(ret_dict)
        self.mox.ReplayAll()

        ret_val = api.fwaas.policy_get(self.request, exp_policy.id)
        self.assertIsInstance(ret_val, api.fwaas.Policy)
        self.assertEqual(exp_policy.name, ret_val.name)
        self.assertTrue(ret_val.id)
        self.assertFalse(len(ret_val.rules))

    @test.create_stubs({neutronclient: ('update_firewall_policy',)})
    def test_policy_update(self):
        policy = self.fw_policies.first()
        policy_dict = self.api_fw_policies.first()

        policy.name = 'new name'
        policy.description = 'new desc'
        policy.shared = True
        policy.audited = False

        policy_dict['name'] = 'new name'
        policy_dict['description'] = 'new desc'
        policy_dict['shared'] = True
        policy_dict['audited'] = False

        form_data = {'name': policy.name,
                     'description': policy.description,
                     'shared': policy.shared,
                     'audited': policy.audited
                     }

        form_dict = {'firewall_policy': form_data}
        ret_dict = {'firewall_policy': policy_dict}

        neutronclient.update_firewall_policy(
            policy.id, form_dict).AndReturn(ret_dict)
        self.mox.ReplayAll()

        ret_val = api.fwaas.policy_update(self.request,
                                          policy.id, **form_data)
        self.assertIsInstance(ret_val, api.fwaas.Policy)
        self.assertEqual(policy.name, ret_val.name)
        self.assertTrue(ret_val.id)

    @test.create_stubs({neutronclient: ('firewall_policy_insert_rule',)})
    def test_policy_insert_rule(self):
        policy = self.fw_policies.first()
        policy_dict = self.api_fw_policies.first()

        new_rule_id = 'h0881d38-c3eb-4fee-9763-12de3338041d'
        policy.firewall_rules.append(new_rule_id)
        policy_dict['firewall_rules'].append(new_rule_id)

        body = {'firewall_rule_id': new_rule_id,
                'insert_before': policy.firewall_rules[1],
                'insert_after': policy.firewall_rules[0]}

        neutronclient.firewall_policy_insert_rule(
            policy.id, body).AndReturn(policy_dict)
        self.mox.ReplayAll()

        ret_val = api.fwaas.policy_insert_rule(self.request,
                                               policy.id, **body)
        self.assertIn(new_rule_id, ret_val.firewall_rules)

    @test.create_stubs({neutronclient: ('firewall_policy_remove_rule',)})
    def test_policy_remove_rule(self):
        policy = self.fw_policies.first()
        policy_dict = self.api_fw_policies.first()

        remove_rule_id = policy.firewall_rules[0]
        policy_dict['firewall_rules'].remove(remove_rule_id)

        body = {'firewall_rule_id': remove_rule_id}

        neutronclient.firewall_policy_remove_rule(
            policy.id, body).AndReturn(policy_dict)
        self.mox.ReplayAll()

        ret_val = api.fwaas.policy_remove_rule(self.request,
                                               policy.id, **body)
        self.assertNotIn(remove_rule_id, ret_val.firewall_rules)

    @test.create_stubs({neutronclient: ('create_firewall', )})
    def test_firewall_create(self):
        firewall = self.firewalls.first()
        firewall_dict = self.api_firewalls.first()

        form_data = {'name': firewall.name,
                     'description': firewall.description,
                     'firewall_policy_id': firewall.firewall_policy_id,
                     'shared': firewall.shared,
                     'admin_state_up': firewall.admin_state_up
                     }

        form_dict = {'firewall': form_data}
        ret_dict = {'firewall': firewall_dict}
        neutronclient.create_firewall(form_dict).AndReturn(ret_dict)
        self.mox.ReplayAll()

        ret_val = api.fwaas.firewall_create(self.request, **form_data)
        self.assertIsInstance(ret_val, api.fwaas.Firewall)
        self.assertEqual(firewall.name, ret_val.name)
        self.assertTrue(ret_val.id)

    @test.create_stubs({neutronclient: ('list_firewalls',
                                        'list_firewall_policies')})
    def test_firewall_list(self):
        exp_firewalls = self.firewalls.list()
        firewalls_dict = {'firewalls': self.api_firewalls.list()}
        policies_dict = {'firewall_policies': self.api_fw_policies.list()}

        neutronclient.list_firewalls().AndReturn(firewalls_dict)
        neutronclient.list_firewall_policies().AndReturn(policies_dict)
        self.mox.ReplayAll()

        ret_val = api.fwaas.firewall_list(self.request)
        for (v, d) in zip(ret_val, exp_firewalls):
            self.assertIsInstance(v, api.fwaas.Firewall)
            self.assertEqual(v.name, d.name)
            self.assertTrue(v.id)
            self.assertEqual(v.policy.id, d.firewall_policy_id)
            self.assertEqual(v.policy.name, d.policy.name)

    @test.create_stubs({neutronclient: ('show_firewall',
                                        'show_firewall_policy')})
    def test_firewall_get(self):
        exp_firewall = self.firewalls.first()
        ret_dict = {'firewall': self.api_firewalls.first()}
        policy_dict = {'firewall_policy': self.api_fw_policies.first()}

        neutronclient.show_firewall(exp_firewall.id).AndReturn(ret_dict)
        neutronclient.show_firewall_policy(
            exp_firewall.firewall_policy_id).AndReturn(policy_dict)
        self.mox.ReplayAll()

        ret_val = api.fwaas.firewall_get(self.request, exp_firewall.id)
        self.assertIsInstance(ret_val, api.fwaas.Firewall)
        self.assertEqual(exp_firewall.name, ret_val.name)
        self.assertTrue(ret_val.id)
        self.assertEqual(ret_val.policy.id, exp_firewall.firewall_policy_id)
        self.assertEqual(ret_val.policy.name, exp_firewall.policy.name)

    @test.create_stubs({neutronclient: ('update_firewall',)})
    def test_firewall_update(self):
        firewall = self.firewalls.first()
        firewall_dict = self.api_firewalls.first()

        firewall.name = 'new name'
        firewall.description = 'new desc'
        firewall.admin_state_up = False

        firewall_dict['name'] = 'new name'
        firewall_dict['description'] = 'new desc'
        firewall_dict['admin_state_up'] = False

        form_data = {'name': firewall.name,
                     'description': firewall.description,
                     'admin_state_up': firewall.admin_state_up
                     }

        form_dict = {'firewall': form_data}
        ret_dict = {'firewall': firewall_dict}

        neutronclient.update_firewall(
            firewall.id, form_dict).AndReturn(ret_dict)
        self.mox.ReplayAll()

        ret_val = api.fwaas.firewall_update(self.request,
                                            firewall.id, **form_data)
        self.assertIsInstance(ret_val, api.fwaas.Firewall)
        self.assertEqual(firewall.name, ret_val.name)
        self.assertTrue(ret_val.id)
