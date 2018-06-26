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


class TestAdminVolumeTypes(helpers.AdminTestCase):
    VOLUME_TYPE_NAME = helpers.gen_random_resource_name("volume_type")

    def test_volume_type_create_delete(self):
        """This test case checks create, delete volume type:

        Steps:
        1. Login to Horizon Dashboard as admin user
        2. Navigate to Admin -> Volume -> Volume Types page
        3. Create new volume type
        4. Check that the volume type is in the list
        5. Check that no Error messages present
        6. Delete the volume type
        7. Check that the volume type is absent in the list
        8. Check that no Error messages present
        """
        volume_types_page = self.home_pg.go_to_admin_volume_volumetypespage()

        volume_types_page.create_volume_type(self.VOLUME_TYPE_NAME)

        self.assertTrue(
            volume_types_page.find_message_and_dismiss(messages.SUCCESS))
        self.assertFalse(
            volume_types_page.find_message_and_dismiss(messages.ERROR))
        self.assertTrue(volume_types_page.is_volume_type_present(
            self.VOLUME_TYPE_NAME))

        volume_types_page.delete_volume_type(self.VOLUME_TYPE_NAME)

        self.assertTrue(
            volume_types_page.find_message_and_dismiss(messages.SUCCESS))
        self.assertFalse(
            volume_types_page.find_message_and_dismiss(messages.ERROR))
        self.assertTrue(volume_types_page.is_volume_type_deleted(
            self.VOLUME_TYPE_NAME))


class TestQoSSpec(helpers.AdminTestCase):
    QOS_SPEC_NAME = helpers.gen_random_resource_name("qos_spec")

    def test_qos_spec_create_delete(self):
        """tests the QoS Spec creation and deletion functionality

        * creates a new QoS Spec
        * verifies the QoS Spec appears in the QoS Specs table
        * deletes the newly created QoS Spec
        * verifies the QoS Spec does not appear in the table after deletion
        """
        qos_spec_page = self.home_pg.go_to_admin_volume_volumetypespage()

        qos_spec_page.create_qos_spec(self.QOS_SPEC_NAME)
        self.assertTrue(
            qos_spec_page.find_message_and_dismiss(messages.SUCCESS))
        self.assertFalse(
            qos_spec_page.find_message_and_dismiss(messages.ERROR))
        self.assertTrue(qos_spec_page.is_qos_spec_present(self.QOS_SPEC_NAME))

        qos_spec_page.delete_qos_specs(self.QOS_SPEC_NAME)
        self.assertTrue(
            qos_spec_page.find_message_and_dismiss(messages.SUCCESS))
        self.assertFalse(
            qos_spec_page.find_message_and_dismiss(messages.ERROR))
        self.assertFalse(qos_spec_page.is_qos_spec_present(self.QOS_SPEC_NAME))

    def test_qos_spec_edit_consumer(self):
        """tests Edit Consumer of QoS Spec functionality

        * creates a new QoS Spec
        * verifies the QoS Spec appears in the QoS Specs table
        * edit consumer of created QoS Spec (check all options - front-end,
          both, back-end)
        * verifies current consumer of the QoS Spec in the QoS Specs table
        * deletes the newly created QoS Spec
        * verifies the QoS Spec does not appear in the table after deletion
        """
        qos_spec_name = helpers.gen_random_resource_name("qos_spec")
        qos_spec_page = self.home_pg.go_to_admin_volume_volumetypespage()
        nova_compute_consumer = 'front-end'
        both_consumers = 'both'
        cinder_consumer = 'back-end'

        qos_spec_page.create_qos_spec(qos_spec_name)
        self.assertTrue(
            qos_spec_page.find_message_and_dismiss(messages.SUCCESS))
        self.assertFalse(
            qos_spec_page.find_message_and_dismiss(messages.ERROR))
        self.assertTrue(qos_spec_page.is_qos_spec_present(qos_spec_name))

        qos_spec_page.edit_consumer(qos_spec_name, nova_compute_consumer)
        self.assertTrue(
            qos_spec_page.find_message_and_dismiss(messages.SUCCESS))
        self.assertFalse(
            qos_spec_page.find_message_and_dismiss(messages.ERROR))
        self.assertEqual(
            qos_spec_page.get_consumer(qos_spec_name), nova_compute_consumer)

        qos_spec_page.edit_consumer(qos_spec_name, both_consumers)
        self.assertTrue(
            qos_spec_page.find_message_and_dismiss(messages.SUCCESS))
        self.assertFalse(
            qos_spec_page.find_message_and_dismiss(messages.ERROR))
        self.assertEqual(
            qos_spec_page.get_consumer(qos_spec_name), both_consumers)

        qos_spec_page.edit_consumer(qos_spec_name, cinder_consumer)
        self.assertTrue(
            qos_spec_page.find_message_and_dismiss(messages.SUCCESS))
        self.assertFalse(
            qos_spec_page.find_message_and_dismiss(messages.ERROR))
        self.assertEqual(
            qos_spec_page.get_consumer(qos_spec_name), cinder_consumer)

        qos_spec_page.delete_qos_specs(qos_spec_name)
        self.assertTrue(
            qos_spec_page.find_message_and_dismiss(messages.SUCCESS))
        self.assertFalse(
            qos_spec_page.find_message_and_dismiss(messages.ERROR))
        self.assertFalse(qos_spec_page.is_qos_spec_present(qos_spec_name))
