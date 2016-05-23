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

from openstack_dashboard.test.integration_tests import decorators
from openstack_dashboard.test.integration_tests import helpers
from openstack_dashboard.test.integration_tests.regions import messages


class TestVolumeSnapshotsBasic(helpers.TestCase):
    """Login as demo user"""
    VOLUME_NAME = helpers.gen_random_resource_name("volume")
    VOLUME_SNAPSHOT_NAME = helpers.gen_random_resource_name("volume_snapshot")

    @property
    def volumes_snapshot_page(self):
        return self.home_pg.go_to_compute_volumes_volumesnapshotspage()

    def setUp(self):
        """Setup: create volume"""
        super(TestVolumeSnapshotsBasic, self).setUp()
        volumes_page = self.home_pg.go_to_compute_volumes_volumespage()
        volumes_page.create_volume(self.VOLUME_NAME)
        volumes_page.find_message_and_dismiss(messages.INFO)
        self.assertTrue(volumes_page.is_volume_status(self.VOLUME_NAME,
                                                      'Available'))

    def test_create_edit_delete_volume_snapshot(self):
        """Test checks create/delete volume snapshot action
            Steps:
            1. Login to Horizon Dashboard
            2. Navigate to Project -> Compute -> Volumes page
            3. Create snapshot for existed volume
            4. Check that no ERROR appears
            5. Check that snapshot is in the list
            6. Check that snapshot has reference to correct volume
            7. Edit snapshot name and description
            8. Delete volume snapshot from proper page
            9. Check that volume snapshot not in the list
        """
        volumes_page = self.home_pg.go_to_compute_volumes_volumespage()
        volumes_snapshot_page = volumes_page.create_volume_snapshot(
            self.VOLUME_NAME, self.VOLUME_SNAPSHOT_NAME)
        self.assertTrue(volumes_page.find_message_and_dismiss(messages.INFO))
        self.assertFalse(volumes_page.find_message_and_dismiss(messages.ERROR))
        self.assertTrue(volumes_snapshot_page.is_volume_snapshot_available(
            self.VOLUME_SNAPSHOT_NAME))
        actual_volume_name = volumes_snapshot_page.get_volume_name(
            self.VOLUME_SNAPSHOT_NAME)
        self.assertEqual(self.VOLUME_NAME, actual_volume_name)

        new_name = "new_" + self.VOLUME_SNAPSHOT_NAME
        volumes_snapshot_page = \
            self.home_pg.go_to_compute_volumes_volumesnapshotspage()
        volumes_snapshot_page.edit_snapshot(self.VOLUME_SNAPSHOT_NAME,
                                            new_name, "description")
        self.assertTrue(
            volumes_snapshot_page.find_message_and_dismiss(messages.INFO))
        self.assertFalse(
            volumes_snapshot_page.find_message_and_dismiss(messages.ERROR))
        self.assertTrue(volumes_snapshot_page.
                        is_volume_snapshot_available(new_name))

        volumes_snapshot_page = self.volumes_snapshot_page
        volumes_snapshot_page.delete_volume_snapshot(new_name)
        self.assertTrue(
            volumes_snapshot_page.find_message_and_dismiss(messages.SUCCESS))
        self.assertFalse(
            volumes_snapshot_page.find_message_and_dismiss(messages.ERROR))
        self.assertTrue(volumes_snapshot_page.is_volume_snapshot_deleted(
            new_name))

    def test_volume_snapshots_pagination(self):
        """This test checks volumes snapshots pagination
            Steps:
            1) Login to Horizon Dashboard
            2) Go to Project -> Compute -> Volumes -> Volumes tab, create
            volumes and 3 snapshots
            3) Navigate to user settings page
            4) Change 'Items Per Page' value to 1
            5) Go to Project -> Compute -> Volumes -> Volumes Snapshot tab
            or Admin -> System -> Volumes -> Volumes Snapshot tab
            (depends on user)
            6) Check that only 'Next' link is available, only one snapshot is
            available (and it has correct name)
            7) Click 'Next' and check that both 'Prev' and 'Next' links are
            available, only one snapshot is available (and it has correct name)
            8) Click 'Next' and check that only 'Prev' link is available,
            only one snapshot is visible (and it has correct name)
            9) Click 'Prev' and check result (should be the same as for step7)
            10) Click 'Prev' and check result (should be the same as for step6)
            11) Go to user settings page and restore 'Items Per Page'
            12) Delete created snapshots and volumes
        """
        volumes_page = self.home_pg.go_to_compute_volumes_volumespage()
        count = 3
        items_per_page = 1
        snapshot_names = ["{0}_{1}".format(self.VOLUME_SNAPSHOT_NAME, i) for i
                          in range(count)]
        for i, name in enumerate(snapshot_names):
            volumes_snapshot_page = volumes_page.create_volume_snapshot(
                self.VOLUME_NAME, name)
            volumes_page.find_message_and_dismiss(messages.INFO)
            self.assertTrue(
                volumes_snapshot_page.is_volume_snapshot_available(name))
            if i < count - 1:
                volumes_snapshot_page.switch_to_volumes_tab()

        first_page_definition = {'Next': True, 'Prev': False,
                                 'Count': items_per_page,
                                 'Names': [snapshot_names[2]]}
        second_page_definition = {'Next': True, 'Prev': True,
                                  'Count': items_per_page,
                                  'Names': [snapshot_names[1]]}
        third_page_definition = {'Next': False, 'Prev': True,
                                 'Count': items_per_page,
                                 'Names': [snapshot_names[0]]}

        settings_page = self.home_pg.go_to_settings_usersettingspage()
        settings_page.change_pagesize(items_per_page)
        settings_page.find_message_and_dismiss(messages.SUCCESS)

        volumes_snapshot_page = self.volumes_snapshot_page
        volumes_snapshot_page.volumesnapshots_table.assert_definition(
            first_page_definition)

        volumes_snapshot_page.volumesnapshots_table.turn_next_page()
        volumes_snapshot_page.volumesnapshots_table.assert_definition(
            second_page_definition)

        volumes_snapshot_page.volumesnapshots_table.turn_next_page()
        volumes_snapshot_page.volumesnapshots_table.assert_definition(
            third_page_definition)

        volumes_snapshot_page.volumesnapshots_table.turn_prev_page()
        volumes_snapshot_page.volumesnapshots_table.assert_definition(
            second_page_definition)

        volumes_snapshot_page.volumesnapshots_table.turn_prev_page()
        volumes_snapshot_page.volumesnapshots_table.assert_definition(
            first_page_definition)

        settings_page = self.home_pg.go_to_settings_usersettingspage()
        settings_page.change_pagesize()
        settings_page.find_message_and_dismiss(messages.SUCCESS)

        volumes_snapshot_page = self.volumes_snapshot_page
        volumes_snapshot_page.delete_volume_snapshots(snapshot_names)
        volumes_snapshot_page.find_message_and_dismiss(messages.SUCCESS)
        for name in snapshot_names:
            volumes_snapshot_page.is_volume_snapshot_deleted(name)

    def tearDown(self):
        """Clean up: delete volume"""
        volumes_snapshot_page = \
            self.home_pg.go_to_compute_volumes_volumesnapshotspage()
        volumes_page = volumes_snapshot_page.switch_to_volumes_tab()
        volumes_page.delete_volume(self.VOLUME_NAME)
        volumes_page.find_message_and_dismiss(messages.SUCCESS)
        self.assertTrue(volumes_page.is_volume_deleted(self.VOLUME_NAME))
        super(TestVolumeSnapshotsBasic, self).tearDown()


class TestVolumeSnapshotsAdmin(helpers.AdminTestCase,
                               TestVolumeSnapshotsBasic):
    """Login as admin user"""
    VOLUME_NAME = helpers.gen_random_resource_name("volume")
    VOLUME_SNAPSHOT_NAME = helpers.gen_random_resource_name("volume_snapshot")

    @property
    def volumes_snapshot_page(self):
        return self.home_pg.go_to_system_volumes_volumesnapshotspage()

    @decorators.skip_because(bugs=['1584057'])
    def test_create_edit_delete_volume_snapshot(self):
        super(TestVolumeSnapshotsAdmin, self).\
            test_create_edit_delete_volume_snapshot()

    @decorators.skip_because(bugs=['1584057'])
    def test_volume_snapshots_pagination(self):
        super(TestVolumeSnapshotsAdmin, self).\
            test_volume_snapshots_pagination()


class TestVolumeSnapshotsAdvanced(helpers.TestCase):
    """Login as demo user"""
    VOLUME_NAME = helpers.gen_random_resource_name("volume")
    VOLUME_SNAPSHOT_NAME = helpers.gen_random_resource_name("volume_snapshot")

    @property
    def volumes_snapshot_page(self):
        return self.home_pg.go_to_compute_volumes_volumesnapshotspage()

    def setUp(self):
        """Setup: create volume"""
        super(TestVolumeSnapshotsAdvanced, self).setUp()
        volumes_page = self.home_pg.go_to_compute_volumes_volumespage()
        volumes_page.create_volume(self.VOLUME_NAME)
        volumes_page.find_message_and_dismiss(messages.INFO)
        self.assertTrue(volumes_page.is_volume_status(self.VOLUME_NAME,
                                                      'Available'))

    def test_create_volume_from_snapshot(self):
        """Test checks possibility to create volume from snapshot
            Steps:
            1. Login to Horizon Dashboard as regular user
            2. Navigate to Project -> Compute -> Volumes page
            3. Create snapshot for existed volume
            4. Create new volume from snapshot
            5. Check the volume is created and has 'Available' status
            6. Delete volume snapshot
            7. Delete volume
        """
        volumes_page = self.home_pg.go_to_compute_volumes_volumespage()
        volumes_snapshot_page = volumes_page.create_volume_snapshot(
            self.VOLUME_NAME, self.VOLUME_SNAPSHOT_NAME)
        self.assertTrue(volumes_page.find_message_and_dismiss(messages.INFO))
        self.assertFalse(volumes_page.find_message_and_dismiss(messages.ERROR))
        self.assertTrue(volumes_snapshot_page.is_volume_snapshot_available(
            self.VOLUME_SNAPSHOT_NAME))

        new_volume = 'new_' + self.VOLUME_NAME
        volumes_snapshot_page.create_volume_from_snapshot(
            self.VOLUME_SNAPSHOT_NAME, new_volume)
        self.assertTrue(volumes_page.is_volume_present(new_volume))
        self.assertTrue(volumes_page.is_volume_status(new_volume, 'Available'))

        volumes_snapshot_page = self.volumes_snapshot_page
        volumes_snapshot_page.delete_volume_snapshot(self.VOLUME_SNAPSHOT_NAME)
        self.assertTrue(
            volumes_snapshot_page.find_message_and_dismiss(messages.SUCCESS))
        self.assertFalse(
            volumes_snapshot_page.find_message_and_dismiss(messages.ERROR))
        self.assertTrue(volumes_snapshot_page.is_volume_snapshot_deleted(
            self.VOLUME_SNAPSHOT_NAME))

        volumes_page = volumes_snapshot_page.switch_to_volumes_tab()
        volumes_page.delete_volume(new_volume)
        self.assertTrue(
            volumes_page.find_message_and_dismiss(messages.SUCCESS))
        self.assertFalse(volumes_page.find_message_and_dismiss(messages.ERROR))
        self.assertTrue(volumes_page.is_volume_deleted(new_volume))

    def tearDown(self):
        """Clean up: delete volume"""
        volumes_snapshot_page = \
            self.home_pg.go_to_compute_volumes_volumesnapshotspage()
        volumes_page = volumes_snapshot_page.switch_to_volumes_tab()
        volumes_page.delete_volume(self.VOLUME_NAME)
        self.assertTrue(
            volumes_page.find_message_and_dismiss(messages.SUCCESS))
        self.assertFalse(volumes_page.find_message_and_dismiss(messages.ERROR))
        self.assertTrue(volumes_page.is_volume_deleted(self.VOLUME_NAME))
        super(TestVolumeSnapshotsAdvanced, self).tearDown()
