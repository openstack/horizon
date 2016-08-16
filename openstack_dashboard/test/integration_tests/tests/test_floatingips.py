# Copyright 2015 Hewlett-Packard Development Company, L.P
# All Rights Reserved.
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

from openstack_dashboard.test.integration_tests import helpers
from openstack_dashboard.test.integration_tests.regions import messages


class TestFloatingip(helpers.TestCase):
    """Checks that the user is able to allocate/release floatingip."""

    def test_floatingip(self):
        floatingip_page = \
            self.home_pg.go_to_compute_accessandsecurity_floatingipspage()
        floating_ip = floatingip_page.allocate_floatingip()
        self.assertTrue(
            floatingip_page.find_message_and_dismiss(messages.SUCCESS))
        self.assertFalse(
            floatingip_page.find_message_and_dismiss(messages.ERROR))
        self.assertTrue(floatingip_page.is_floatingip_present(floating_ip))

        floatingip_page.release_floatingip(floating_ip)
        self.assertTrue(
            floatingip_page.find_message_and_dismiss(messages.SUCCESS))
        self.assertFalse(
            floatingip_page.find_message_and_dismiss(messages.ERROR))
        self.assertFalse(floatingip_page.is_floatingip_present(floating_ip))


class TestFloatingipAssociateDisassociate(helpers.TestCase):
    """Checks that the user is able to Associate/Disassociate floatingip."""

    def test_floatingip_associate_disassociate(self):
        instance_name = helpers.gen_random_resource_name('instance',
                                                         timestamp=False)
        instances_page = self.home_pg.go_to_compute_instancespage()
        instances_page.create_instance(instance_name)
        self.assertTrue(
            instances_page.find_message_and_dismiss(messages.SUCCESS))
        self.assertFalse(
            instances_page.find_message_and_dismiss(messages.ERROR))
        self.assertTrue(instances_page.is_instance_active(instance_name))
        instance_ipv4 = instances_page.get_fixed_ipv4(instance_name)
        instance_info = "{} {}".format(instance_name, instance_ipv4)

        floatingip_page = \
            self.home_pg.go_to_compute_accessandsecurity_floatingipspage()
        floating_ip = floatingip_page.allocate_floatingip()
        self.assertTrue(
            floatingip_page.find_message_and_dismiss(messages.SUCCESS))
        self.assertFalse(
            floatingip_page.find_message_and_dismiss(messages.ERROR))
        self.assertTrue(floatingip_page.is_floatingip_present(floating_ip))

        self.assertEqual('-', floatingip_page.get_fixed_ip(floating_ip))
        floatingip_page.associate_floatingip(floating_ip, instance_name,
                                             instance_ipv4)
        self.assertTrue(
            floatingip_page.find_message_and_dismiss(messages.SUCCESS))
        self.assertFalse(
            floatingip_page.find_message_and_dismiss(messages.ERROR))
        self.assertEqual(instance_info,
                         floatingip_page.get_fixed_ip(floating_ip))

        floatingip_page.disassociate_floatingip(floating_ip)
        self.assertTrue(
            floatingip_page.find_message_and_dismiss(messages.SUCCESS))
        self.assertFalse(
            floatingip_page.find_message_and_dismiss(messages.ERROR))
        self.assertEqual('-', floatingip_page.get_fixed_ip(floating_ip))

        floatingip_page.release_floatingip(floating_ip)
        self.assertTrue(
            floatingip_page.find_message_and_dismiss(messages.SUCCESS))
        self.assertFalse(
            floatingip_page.find_message_and_dismiss(messages.ERROR))
        self.assertFalse(floatingip_page.is_floatingip_present(floating_ip))

        instances_page = self.home_pg.go_to_compute_instancespage()
        instances_page.delete_instance(instance_name)
        self.assertTrue(
            instances_page.find_message_and_dismiss(messages.SUCCESS))
        self.assertFalse(
            instances_page.find_message_and_dismiss(messages.ERROR))
        self.assertTrue(instances_page.is_instance_deleted(instance_name))
