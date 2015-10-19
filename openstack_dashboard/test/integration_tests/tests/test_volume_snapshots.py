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

VOLUME_NAME = helpers.gen_random_resource_name("volume")
VOLUME_SNAPSHOT_NAME = helpers.gen_random_resource_name("volume_snapshot")


class TestVolumeSnapshots(helpers.TestCase):
    def setUp(self):
        """Setup for test_create_delete_volume_snapshot: create volume"""
        super(TestVolumeSnapshots, self).setUp()
        self.volumes_page = self.home_pg.go_to_compute_volumes_volumespage()
        self.volumes_page.create_volume(VOLUME_NAME)
        self.assertTrue(
            self.volumes_page.find_message_and_dismiss(messages.INFO))
        self.assertFalse(
            self.volumes_page.find_message_and_dismiss(messages.ERROR))
        self.assertTrue(self.volumes_page.is_volume_status(VOLUME_NAME,
                                                           'Available'))

    def test_create_edit_delete_volume_snapshot(self):
        """Test checks create/delete volume snapshot action under
            non-admin user
            Steps:
            1. Login to Horizon Dashboard as horizon user
            2. Navigate to Project -> Compute -> Volumes page
            3. Create snapshot for existed volume
            4. Check that no ERROR appears
            5. Check that snapshot is in the list
            6. Check that snapshot has reference to correct volume
            7. Edit snapshot name and description
            8. Delete volume snapshot
            9. Check that volume snapshot not in the list
        """
        row = self.volumes_page._get_row_with_volume_name(VOLUME_NAME)
        self.volumes_page.create_volume_snapshot(row, VOLUME_SNAPSHOT_NAME)
        self.assertTrue(
            self.volumes_page.find_message_and_dismiss(messages.INFO))
        self.assertFalse(
            self.volumes_page.find_message_and_dismiss(messages.ERROR))
        volumes_snapshot_page = self.home_pg. \
            go_to_compute_volumes_volumesnapshotspage()
        self.assertTrue(
            volumes_snapshot_page.is_volume_snapshot_available(
                VOLUME_SNAPSHOT_NAME))
        actual_volume_name = \
            volumes_snapshot_page.get_volume_name(VOLUME_SNAPSHOT_NAME)
        self.assertEqual(VOLUME_NAME, actual_volume_name)

        new_name = "new_" + VOLUME_SNAPSHOT_NAME
        volumes_snapshot_page.edit_snapshot(VOLUME_SNAPSHOT_NAME,
                                            new_name, "description")
        self.assertTrue(
            volumes_snapshot_page.find_message_and_dismiss(messages.INFO))
        self.assertFalse(
            volumes_snapshot_page.find_message_and_dismiss(messages.ERROR))
        self.assertTrue(volumes_snapshot_page.
                        is_volume_snapshot_available(new_name))

        volumes_snapshot_page.delete_volume_snapshot(new_name)
        self.assertTrue(
            volumes_snapshot_page.find_message_and_dismiss(messages.SUCCESS))
        self.assertFalse(
            volumes_snapshot_page.find_message_and_dismiss(messages.ERROR))
        self.assertTrue(volumes_snapshot_page.is_volume_snapshot_deleted(
            new_name))

    def test_create_volume_from_snapshot(self):
        """Test checks possibility to create volume from snapshot
            Steps:
            1. Login to Horizon Dashboard as horizon user
            2. Navigate to Project -> Compute -> Volumes page
            3. Create snapshot for existed volume
            4. Create new volume from snapshot
            5. Check the volume is created and has 'Available' status
            6. Delete volume snapshot
            7. Delete volume
        """
        row = self.volumes_page._get_row_with_volume_name(VOLUME_NAME)
        self.volumes_page.create_volume_snapshot(row, VOLUME_SNAPSHOT_NAME)
        self.assertTrue(
            self.volumes_page.find_message_and_dismiss(messages.INFO))
        self.assertFalse(
            self.volumes_page.find_message_and_dismiss(messages.ERROR))
        volumes_snapshot_page = self.home_pg. \
            go_to_compute_volumes_volumesnapshotspage()
        self.assertTrue(
            volumes_snapshot_page.is_volume_snapshot_available(
                VOLUME_SNAPSHOT_NAME))

        new_volume = 'new_' + VOLUME_NAME
        volumes_snapshot_page.create_volume_from_snapshot(VOLUME_SNAPSHOT_NAME,
                                                          new_volume)
        self.assertTrue(
            self.volumes_page.is_volume_present(new_volume))
        self.assertTrue(
            self.volumes_page.is_volume_status(new_volume, 'Available'))

        volumes_snapshot_page = self.home_pg.\
            go_to_compute_volumes_volumesnapshotspage()
        volumes_snapshot_page.delete_volume_snapshot(VOLUME_SNAPSHOT_NAME)
        self.assertTrue(
            volumes_snapshot_page.find_message_and_dismiss(messages.SUCCESS))
        self.assertFalse(
            volumes_snapshot_page.find_message_and_dismiss(messages.ERROR))
        self.assertTrue(volumes_snapshot_page.is_volume_snapshot_deleted(
            VOLUME_SNAPSHOT_NAME))

        volumes_page = volumes_snapshot_page.switch_to_volumes_tab()
        volumes_page.delete_volume(new_volume)
        self.assertTrue(
            volumes_page.find_message_and_dismiss(messages.SUCCESS))
        self.assertFalse(
            self.volumes_page.find_message_and_dismiss(messages.ERROR))
        self.assertTrue(
            self.volumes_page.is_volume_deleted(new_volume))

    def tearDown(self):
        """Clean up after test_create_delete_volume_snapshot: delete volume"""
        volumes_snapshot_page = self.home_pg. \
            go_to_compute_volumes_volumesnapshotspage()
        volumes_page = volumes_snapshot_page.switch_to_volumes_tab()
        volumes_page.delete_volume(VOLUME_NAME)
        self.assertTrue(
            volumes_page.find_message_and_dismiss(messages.SUCCESS))
        self.assertFalse(
            self.volumes_page.find_message_and_dismiss(messages.ERROR))
        self.assertTrue(
            self.volumes_page.is_volume_deleted(VOLUME_NAME))
        super(TestVolumeSnapshots, self).tearDown()


class TestAdminVolumeSnapshots(helpers.AdminTestCase):
    def setUp(self):
        """Setup for test_delete_volume_snapshot_through_admin:
            create volume and volume snapshot
        """
        super(TestAdminVolumeSnapshots, self).setUp()
        self.volumes_page = self.home_pg.go_to_compute_volumes_volumespage()
        self.volumes_page.create_volume(VOLUME_NAME)
        self.assertTrue(
            self.volumes_page.find_message_and_dismiss(messages.INFO))
        self.assertFalse(
            self.volumes_page.find_message_and_dismiss(messages.ERROR))
        self.assertTrue(self.volumes_page.is_volume_status(VOLUME_NAME,
                                                           'Available'))

        row = self.volumes_page._get_row_with_volume_name(VOLUME_NAME)
        self.volumes_page.create_volume_snapshot(row, VOLUME_SNAPSHOT_NAME)
        self.assertTrue(
            self.volumes_page.find_message_and_dismiss(messages.INFO))
        self.assertFalse(
            self.volumes_page.find_message_and_dismiss(messages.ERROR))
        volumes_snapshot_page = self.home_pg. \
            go_to_compute_volumes_volumesnapshotspage()
        self.assertTrue(
            volumes_snapshot_page.is_volume_snapshot_available(
                VOLUME_SNAPSHOT_NAME))

    def test_delete_volume_snapshot_through_admin(self):
        """Test checks delete volume snapshot action under
            non-admin user
            Steps:
            1. Login to Horizon Dashboard as horizon user
            2. Navigate to Admin -> Volumes -> Volumes snapshots
            3. Delete volume snapshot
            4. Check that volume snapshot not in the list
        """
        volumes_admin_snapshot_page = self.home_pg. \
            go_to_system_volumes_volumesnapshotspage()
        self.assertTrue(
            volumes_admin_snapshot_page.is_volume_snapshot_available(
                VOLUME_SNAPSHOT_NAME))
        actual_volume_name = \
            volumes_admin_snapshot_page.get_volume_name(VOLUME_SNAPSHOT_NAME)
        self.assertEqual(VOLUME_NAME, actual_volume_name)

        volumes_admin_snapshot_page.delete_volume_snapshot(
            VOLUME_SNAPSHOT_NAME)
        self.assertTrue(
            volumes_admin_snapshot_page.find_message_and_dismiss(
                messages.SUCCESS))
        self.assertFalse(
            volumes_admin_snapshot_page.find_message_and_dismiss(
                messages.ERROR))
        self.assertTrue(volumes_admin_snapshot_page.
                        is_volume_snapshot_deleted(VOLUME_SNAPSHOT_NAME))

    def tearDown(self):
        """Clean up after test_delete_volume_snapshot_through_admin:
            delete volume
        """
        volumes_snapshot_page = self.home_pg. \
            go_to_compute_volumes_volumesnapshotspage()
        volumes_page = volumes_snapshot_page.switch_to_volumes_tab()
        volumes_page.delete_volume(VOLUME_NAME)
        self.assertTrue(
            volumes_page.find_message_and_dismiss(messages.SUCCESS))
        self.assertFalse(
            self.volumes_page.find_message_and_dismiss(messages.ERROR))
        self.assertTrue(
            self.volumes_page.is_volume_deleted(VOLUME_NAME))
        super(TestAdminVolumeSnapshots, self).tearDown()
