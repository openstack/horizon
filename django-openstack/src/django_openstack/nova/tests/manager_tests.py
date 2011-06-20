# vim: tabstop=4 shiftwidth=4 softtabstop=4

import boto
import mox

from boto.ec2.connection import EC2Connection
from django import test
from django.conf import settings
from django_openstack.core import connection
from django_openstack.nova.manager import ProjectManager
from mox import And, ContainsKeyValue, IgnoreArg, IsA, StrContains
from nova_adminclient import client as nova_client


TEST_DESCRIPTION = 'testDescription'
TEST_FROM_PORT = 1024
TEST_IMAGE_ID = 1
TEST_INSTANCE_ID = 1
TEST_INSTANCE_IDS = range(8)
TEST_INSTANCE_NAME = 'testInstance'
TEST_INSTANCE_TYPE = 'm1.small'
TEST_KEYPAIR_BAD_NAMES = ['vpn-key']
TEST_KEYPAIR_NAMES = ['key1', 'key2', 'key3', 'key4']
TEST_PROJECT_DESCRIPTION = 'testDescription'
TEST_PROJECT_MANAGER_ID = 100
TEST_PROJECT_MEMBER_IDS = []
TEST_PROJECT_NAME = 'testProject'
TEST_PROTOCOL = 'tcp'
TEST_REGION_ENDPOINT = 'http://testServer:8773/services/Cloud'
TEST_REGION_NAME = 'testRegion'
TEST_REGION = {'endpoint': TEST_REGION_ENDPOINT, 'name': TEST_REGION_NAME}
TEST_RETURN = 'testReturn'
TEST_SECURITY_GROUP_NAME = 'testGroup'
TEST_SIZE = 3
TEST_SNAPSHOT = 'aSnapshot'
TEST_TO_PORT = 2048
TEST_USER = 'testUser'
TEST_OTHERUSER = 'otherUser'
TEST_VOLUME_ID = 1000
TEST_VOLUME_NAME = 'testVolume'


class ProjectManagerTests(test.TestCase):
    def setUp(self):
        self.mox = mox.Mox()
        project = nova_client.ProjectInfo()
        project.projectname = TEST_PROJECT_NAME
        project.projectManagerId = TEST_PROJECT_MANAGER_ID

        self.manager = ProjectManager(TEST_USER, project, TEST_REGION)

    def tearDown(self):
        self.mox.UnsetStubs()

    def stub_conn_mock(self, count=1):
        '''
        Stubs get_openstack_connection as an EC2Connection and returns the
        EC2Connection mock
        '''
        self.mox.StubOutWithMock(self.manager, 'get_openstack_connection')
        conn_mock = self.mox.CreateMock(EC2Connection)
        for i in range(count):
            self.manager.get_openstack_connection().AndReturn(conn_mock)
        return conn_mock

    def test_get_openstack_connection(self):
        self.mox.StubOutWithMock(connection, 'get_nova_admin_connection')
        admin_mock = self.mox.CreateMock(nova_client.NovaAdminClient)
        admin_mock.connection_for(TEST_USER, TEST_PROJECT_NAME,
                                  clc_url=TEST_REGION_ENDPOINT,
                                  region=TEST_REGION_NAME)
        connection.get_nova_admin_connection().AndReturn(admin_mock)

        self.mox.ReplayAll()

        self.manager.get_openstack_connection()

        self.mox.VerifyAll()

    def test_get_zip(self):
        self.mox.StubOutWithMock(connection, 'get_nova_admin_connection')
        admin_mock = self.mox.CreateMock(nova_client.NovaAdminClient)
        admin_mock.get_zip(TEST_USER, TEST_PROJECT_NAME)
        connection.get_nova_admin_connection().AndReturn(admin_mock)

        self.mox.ReplayAll()

        self.manager.get_zip()

        self.mox.VerifyAll()

    def test_get_images(self):
        def create_fake_image(location='nova', image_type='machine',
                              owner=TEST_USER):
            class fakeimage(object):
                def __init__(self, location, image_type, owner):
                    self.location = str(location)
                    self.type = image_type
                    self.ownerId = owner
            return fakeimage(location, image_type, owner)

        def test_correct_sorting():
            conn_mock = self.stub_conn_mock()

            images_owner_other = [create_fake_image(owner=TEST_OTHERUSER)
                                  for i in range(3)]
            images_owner_self = [create_fake_image() for i in range(3)]
            # images in reverse expected order
            images = images_owner_other + images_owner_self

            conn_mock.get_all_images(image_ids=None).AndReturn(images)

            self.mox.ReplayAll()

            ret_images = self.manager.get_images()
            self.assertEqual(len(ret_images), 6)
            # owner_images should be first
            for image in images_owner_self:
                self.assertTrue(image in ret_images[:3])

            # non-owner_images should be last
            for image in images_owner_other:
                self.assertTrue(image in ret_images[3:])

            self.mox.VerifyAll()
            self.mox.UnsetStubs()

        def test_type_filtering():
            conn_mock = self.stub_conn_mock()

            images_machine = [create_fake_image() for i in range(3)]
            images_fake = [create_fake_image(image_type='fake')
                           for i in range(3)]
            images = images_machine + images_fake

            conn_mock.get_all_images(image_ids=None).AndReturn(images)

            self.mox.ReplayAll()

            ret_images = self.manager.get_images()
            self.assertEqual(len(ret_images), 3)

            for image in ret_images:
                self.assertTrue(image in images_machine)
                self.assertTrue(image not in images_fake)

            self.mox.VerifyAll()
            self.mox.UnsetStubs()

        def test_location_filtering():
            conn_mock = self.stub_conn_mock()

            images_openstack = [create_fake_image(location='openstack/foobar')
                                for i in range(3)]
            images_nova = [create_fake_image(location='nova/foobar')
                           for i in range(3)]

            images = images_openstack + images_nova

            conn_mock.get_all_images(image_ids=None).AndReturn(images)

            self.mox.ReplayAll()

            ret_images = self.manager.get_images()
            self.assertEqual(len(ret_images), 3)

            for image in ret_images:
                self.assertTrue(image in images_nova)
                self.assertTrue(image not in images_openstack)

            self.mox.VerifyAll()
            self.mox.UnsetStubs()

        def test_image_ids_handling():
            conn_mock = self.stub_conn_mock()

            images = [create_fake_image() for i in range(3)]

            conn_mock.get_all_images(
                    image_ids=[TEST_IMAGE_ID]).AndReturn(images)

            self.mox.ReplayAll()

            self.manager.get_images(image_ids=[TEST_IMAGE_ID])

            self.mox.VerifyAll()
            self.mox.UnsetStubs()

        test_correct_sorting()
        test_type_filtering()
        test_location_filtering()
        test_image_ids_handling()

    def test_get_image(self):
        TEST_IMAGE_BAD_ID = TEST_IMAGE_ID + 1
        self.mox.StubOutWithMock(self.manager, 'get_images')
        self.manager.get_images(image_ids=[TEST_IMAGE_ID]).AndReturn(
                [TEST_IMAGE_ID])
        self.manager.get_images(image_ids=[TEST_IMAGE_BAD_ID]).AndReturn([])

        self.mox.ReplayAll()

        image_result = self.manager.get_image(TEST_IMAGE_ID)
        self.assertEqual(TEST_IMAGE_ID, image_result)

        image_result = self.manager.get_image(TEST_IMAGE_BAD_ID)
        self.assertTrue(image_result is None)

        self.mox.VerifyAll()

    def test_deregister_image(self):
        conn_mock = self.stub_conn_mock()
        conn_mock.deregister_image(TEST_IMAGE_ID).AndReturn(TEST_IMAGE_ID)

        self.mox.ReplayAll()

        deregistered_id = self.manager.deregister_image(TEST_IMAGE_ID)

        self.assertEqual(deregistered_id, TEST_IMAGE_ID)

        self.mox.VerifyAll()

    def test_update_image(self):
        TEST_DISPLAY_NAME = 'testDisplayName'

        conn_mock = self.stub_conn_mock(count=2)

        conn_mock.get_object('UpdateImage', And(
                             ContainsKeyValue('ImageId', TEST_IMAGE_ID),
                             ContainsKeyValue('DisplayName',
                                              TEST_DISPLAY_NAME),
                             ContainsKeyValue('Description', TEST_DESCRIPTION)
                             ),
                             boto.ec2.image.Image).AndReturn(TEST_RETURN)
        conn_mock.get_object('UpdateImage', And(
                             ContainsKeyValue('ImageId', TEST_IMAGE_ID),
                             ContainsKeyValue('DisplayName', None),
                             ContainsKeyValue('Description', None)
                             ),
                             boto.ec2.image.Image).AndReturn(TEST_RETURN)

        self.mox.ReplayAll()

        update_result = self.manager.update_image(TEST_IMAGE_ID,
                                  display_name=TEST_DISPLAY_NAME,
                                  description=TEST_DESCRIPTION)

        self.assertEqual(update_result, TEST_RETURN)

        update_result = self.manager.update_image(TEST_IMAGE_ID)

        self.assertEqual(update_result, TEST_RETURN)

        self.mox.VerifyAll()

    def test_modify_image_attribute(self):
        TEST_ATTRIBUTE = 'testAttribute'
        TEST_OPERATION = 'testOperation'
        TEST_GROUPS = 'testGroups'

        conn_mock = self.stub_conn_mock(count=2)

        # Test: default attributes passed
        conn_mock.modify_image_attribute(TEST_IMAGE_ID,
                                         attribute=None,
                                         operation=None,
                                         groups='all').AndReturn(TEST_RETURN)
        # Test: custom attributes passed
        conn_mock.modify_image_attribute(TEST_IMAGE_ID,
                                         attribute=TEST_ATTRIBUTE,
                                         operation=TEST_OPERATION,
                                         groups=TEST_GROUPS
                                        ).AndReturn(TEST_RETURN)

        self.mox.ReplayAll()

        modify_return = self.manager.modify_image_attribute(TEST_IMAGE_ID)
        self.assertEqual(modify_return, TEST_RETURN)

        modify_return = \
                self.manager.modify_image_attribute(TEST_IMAGE_ID,
                                                    attribute=TEST_ATTRIBUTE,
                                                    operation=TEST_OPERATION,
                                                    groups=TEST_GROUPS)
        self.assertEqual(modify_return, TEST_RETURN)

        self.mox.VerifyAll()

    def test_run_instances(self):
        conn_mock = self.stub_conn_mock()

        params = And(ContainsKeyValue('ImageId', TEST_IMAGE_ID),
                     ContainsKeyValue('InstanceType', TEST_INSTANCE_TYPE),
                     ContainsKeyValue('MinCount', 1),
                     ContainsKeyValue('MaxCount', 1),
                     ContainsKeyValue('addressing_type', 'private'),
                     ContainsKeyValue('key_name', 'testKey'),
                     ContainsKeyValue('UserData', 'userData'))

        conn_mock.get_object('RunInstances', params,
                             boto.ec2.instance.Reservation, 
                             verb='POST').AndReturn(TEST_RETURN)

        self.mox.ReplayAll()


        run_return = self.manager.run_instances(TEST_IMAGE_ID,
                                                TEST_INSTANCE_TYPE,
                                                1,
                                                key_name='testKey',
                                                user_data='userData')
        self.assertEqual(run_return, TEST_RETURN)

        self.mox.VerifyAll()

    def test_get_instance_count(self):
        self.mox.StubOutWithMock(self.manager, 'get_instances')

        def valid_instance_list():
            self.manager.get_instances().AndReturn(TEST_INSTANCE_IDS)
            self.mox.ReplayAll()
            self.assertEqual(len(TEST_INSTANCE_IDS),
                             self.manager.get_instance_count())
            self.mox.VerifyAll()
            self.mox.ResetAll()

        def invalid_instance_list():
            self.manager.get_instances().AndReturn(None)
            self.mox.ReplayAll()
            self.assertTrue(self.manager.get_instance_count() is None)
            self.mox.VerifyAll()
            self.mox.ResetAll()

        valid_instance_list()
        invalid_instance_list()

    def get_reservation_mock(self, instance_ids):
        rMock = self.mox.CreateMock(boto.ec2.instance.Reservation)
        instances = []
        for instance_id in instance_ids:
            instance = boto.ec2.instance.Instance()
            instance.id = instance_id
            instances.append(instance)
        rMock.instances = instances

        return rMock

    def get_single_instance_single_reservation(self, instance_id):
        return self.get_reservation_mock([instance_id])

    def get_multiple_instances_multiple_reservations(self, instance_ids):
        rMock1 = \
            self.get_reservation_mock(instance_ids[:len(instance_ids) // 2])
        rMock2 = \
            self.get_reservation_mock(instance_ids[len(instance_ids) // 2:])
        return [rMock1, rMock2]

    def test_get_instances(self):

        def single_instance_single_reservation():
            conn_mock = self.stub_conn_mock()
            rMock = \
                self.get_single_instance_single_reservation(TEST_INSTANCE_ID)
            conn_mock.get_all_instances().AndReturn([rMock])

            self.mox.ReplayAll()

            instances = self.manager.get_instances()
            self.assertEqual(1, len(instances))
            self.assertEqual(TEST_INSTANCE_ID, instances[0].id)

            self.mox.VerifyAll()
            self.mox.ResetAll()

        def multiple_instances_multiple_reservations():
            conn_mock = self.stub_conn_mock()
            rMocks = self.get_multiple_instances_multiple_reservations(
                        TEST_INSTANCE_IDS)

            conn_mock.get_all_instances().AndReturn(rMocks)

            self.mox.ReplayAll()

            instances = self.manager.get_instances()
            self.assertEqual(len(TEST_INSTANCE_IDS), len(instances))
            instance_ids = [instance.id for instance in instances]
            for instance_id in instance_ids:
                self.assertTrue(instance_id in TEST_INSTANCE_IDS)

            self.mox.VerifyAll()
            self.mox.ResetAll()

        single_instance_single_reservation()
        multiple_instances_multiple_reservations()

    def test_get_instance(self):

        def single_instance_single_reservation():
            conn_mock = self.stub_conn_mock()
            rMock = \
                self.get_single_instance_single_reservation(TEST_INSTANCE_ID)
            conn_mock.get_all_instances().AndReturn([rMock])

            self.mox.ReplayAll()

            instance = self.manager.get_instance(TEST_INSTANCE_ID)
            self.assertEqual(instance.id, TEST_INSTANCE_ID)

            self.mox.VerifyAll()
            self.mox.UnsetStubs()

        def multiple_instances_multiple_reservations():
            INDEX = 4
            conn_mock = self.stub_conn_mock()
            rMocks = self.get_multiple_instances_multiple_reservations(
                        TEST_INSTANCE_IDS)
            conn_mock.get_all_instances().AndReturn(rMocks)

            self.mox.ReplayAll()

            instance = self.manager.get_instance(TEST_INSTANCE_IDS[INDEX])
            self.assertEqual(instance.id, TEST_INSTANCE_IDS[INDEX])

            self.mox.VerifyAll()
            self.mox.UnsetStubs()

        def instance_missing():
            conn_mock = self.stub_conn_mock()
            rMock = \
                self.get_single_instance_single_reservation(TEST_INSTANCE_ID)
            conn_mock.get_all_instances().AndReturn([rMock])

            self.mox.ReplayAll()

            instance = self.manager.get_instance(TEST_INSTANCE_ID + 1)
            self.assertTrue(instance is None)

            self.mox.VerifyAll()
            self.mox.UnsetStubs()

        single_instance_single_reservation()
        multiple_instances_multiple_reservations()
        instance_missing()

    def test_update_instance(self):
        conn_mock = self.stub_conn_mock()
        conn_mock.get_object('UpdateInstance', And(
                             ContainsKeyValue('InstanceId',
                                              TEST_INSTANCE_ID),
                             ContainsKeyValue('DisplayName',
                                              TEST_INSTANCE_NAME),
                             ContainsKeyValue('DisplayDescription',
                                              TEST_DESCRIPTION),
                             ),
                boto.ec2.instance.Instance).AndReturn(TEST_RETURN)

        updates = {'nickname': TEST_INSTANCE_NAME,
                   'description': TEST_DESCRIPTION}

        self.mox.ReplayAll()

        retVal = self.manager.update_instance(TEST_INSTANCE_ID, updates)
        self.assertEqual(retVal, TEST_RETURN)

        self.mox.VerifyAll()

    def test_terminate_instance(self):
        conn_mock = self.stub_conn_mock()
        conn_mock.terminate_instances([TEST_INSTANCE_ID])

        self.mox.ReplayAll()

        retval = self.manager.terminate_instance(TEST_INSTANCE_ID)
        self.assertTrue(retval is None)

        self.mox.VerifyAll()

    def test_get_security_groups(self):
        TEST_SECURITY_GROUPS = ['group1', 'group2']

        conn_mock = self.stub_conn_mock()
        conn_mock.get_all_security_groups().AndReturn(TEST_SECURITY_GROUPS)

        self.mox.ReplayAll()

        groups = self.manager.get_security_groups()
        for group in groups:
            self.assertTrue(group in TEST_SECURITY_GROUPS)

    def test_get_security_group(self):
        conn_mock = self.stub_conn_mock(count=2)
        conn_mock.get_all_security_groups(
                groupnames=TEST_SECURITY_GROUP_NAME.encode('ascii')
                ).AndReturn([TEST_RETURN])
        conn_mock.get_all_security_groups(
                groupnames=TEST_SECURITY_GROUP_NAME.encode('ascii')
                ).AndReturn([])

        self.mox.ReplayAll()

        # Something is there
        group = self.manager.get_security_group(TEST_SECURITY_GROUP_NAME)
        self.assertEqual(group, TEST_RETURN)

        # Nothing is there
        group = self.manager.get_security_group(TEST_SECURITY_GROUP_NAME)
        self.assertEqual(group, None)

        self.mox.VerifyAll()

    def test_has_security_group(self):
        self.mox.StubOutWithMock(self.manager, 'get_security_group')

        self.manager.get_security_group(TEST_SECURITY_GROUP_NAME).AndReturn(
                TEST_SECURITY_GROUP_NAME)
        self.manager.get_security_group(TEST_SECURITY_GROUP_NAME).AndReturn(
                None)

        self.mox.ReplayAll()

        # security group exists
        self.assertTrue(
                self.manager.has_security_group(TEST_SECURITY_GROUP_NAME))

        # security group does not exist
        self.assertFalse(
                self.manager.has_security_group(TEST_SECURITY_GROUP_NAME))

        self.mox.VerifyAll()

    def test_create_security_group(self):
        conn_mock = self.stub_conn_mock()

        conn_mock.create_security_group(TEST_SECURITY_GROUP_NAME,
                                        TEST_DESCRIPTION
                                       ).AndReturn(TEST_RETURN)

        self.mox.ReplayAll()

        retval = self.manager.create_security_group(TEST_SECURITY_GROUP_NAME,
                                                    TEST_DESCRIPTION)

        self.assertEqual(retval, TEST_RETURN)

        self.mox.VerifyAll()

    def test_delete_security_group(self):
        conn_mock = self.stub_conn_mock()

        conn_mock.delete_security_group(
                name=TEST_SECURITY_GROUP_NAME).AndReturn(TEST_RETURN)

        self.mox.ReplayAll()

        retval = self.manager.delete_security_group(TEST_SECURITY_GROUP_NAME)

        self.assertEqual(retval, TEST_RETURN)

        self.mox.VerifyAll()

    def test_authorize_security_group(self):
        conn_mock = self.stub_conn_mock()

        conn_mock.authorize_security_group(group_name=TEST_SECURITY_GROUP_NAME,
                                           ip_protocol=TEST_PROTOCOL,
                                           from_port=TEST_FROM_PORT,
                                           to_port=TEST_TO_PORT,
                                           cidr_ip=IgnoreArg()
                                          ).AndReturn(TEST_RETURN)

        self.mox.ReplayAll()

        retval = self.manager.authorize_security_group(
                                              TEST_SECURITY_GROUP_NAME,
                                              TEST_PROTOCOL,
                                              TEST_FROM_PORT,
                                              TEST_TO_PORT
                                              )

        self.assertEqual(retval, TEST_RETURN)

        self.mox.VerifyAll()

    def test_revoke_security_group(self):
        conn_mock = self.stub_conn_mock()

        conn_mock.revoke_security_group(group_name=TEST_SECURITY_GROUP_NAME,
                                        ip_protocol=TEST_PROTOCOL,
                                        from_port=TEST_FROM_PORT,
                                        to_port=TEST_TO_PORT,
                                        cidr_ip=IgnoreArg()
                                       ).AndReturn(TEST_RETURN)

        self.mox.ReplayAll()

        retval = self.manager.revoke_security_group(
                                              TEST_SECURITY_GROUP_NAME,
                                              TEST_PROTOCOL,
                                              TEST_FROM_PORT,
                                              TEST_TO_PORT
                                              )

        self.assertEqual(retval, TEST_RETURN)

        self.mox.VerifyAll()

    def test_get_key_pairs(self):
        def create_key_pair(name):
            class fakekeypair(object):
                def __init__(self, name):
                    self.name = name
            return fakekeypair(name)

        TEST_KEYPAIRS = map(create_key_pair, TEST_KEYPAIR_NAMES)
        TEST_BAD_KEYPAIRS = map(create_key_pair, TEST_KEYPAIR_BAD_NAMES)
        TEST_KEYPAIRS_EMPTY = []

        conn_mock = self.stub_conn_mock(count=3)
        conn_mock.get_all_key_pairs().AndReturn(TEST_KEYPAIRS)
        conn_mock.get_all_key_pairs().AndReturn(TEST_KEYPAIRS +
                                                TEST_BAD_KEYPAIRS)
        conn_mock.get_all_key_pairs().AndReturn(TEST_KEYPAIRS_EMPTY)

        self.mox.ReplayAll()

        # all keys valid
        keypairs = self.manager.get_key_pairs()
        # upgrade to 2.7 to use this instead
        # self.assertItemsEqual(keypairs, TEST_KEYPAIRS)
        for keypair in keypairs:
            self.assertTrue(keypair in TEST_KEYPAIRS,
                    '%s missing from returned keypairs' % keypair.name)

        # special vpn-key should be omitted
        keypairs = self.manager.get_key_pairs()
        for keypair in keypairs:
            self.assertTrue(keypair not in TEST_BAD_KEYPAIRS,
                    '%s present in returned keypairs' % keypair.name)
            self.assertTrue(keypair in TEST_KEYPAIRS,
                    '%s missing from returned keypairs' % keypair.name)

        # empty list
        keypairs = self.manager.get_key_pairs()
        self.assertEqual(len(keypairs), 0)

        self.mox.VerifyAll()

    def test_get_key_pair(self):
        conn_mock = self.stub_conn_mock(count=2)

        conn_mock.get_all_key_pairs(
                keynames=TEST_KEYPAIR_NAMES[0].encode('ascii')).AndReturn(
                        [TEST_RETURN])
        conn_mock.get_all_key_pairs(
                keynames=TEST_KEYPAIR_NAMES[0].encode('ascii')).AndReturn(
                        [])

        self.mox.ReplayAll()

        retval = self.manager.get_key_pair(TEST_KEYPAIR_NAMES[0])
        self.assertEqual(retval, TEST_RETURN)

        retval = self.manager.get_key_pair(TEST_KEYPAIR_NAMES[0])
        self.assertTrue(retval is None)

        self.mox.VerifyAll()

    def test_has_key_pair(self):
        self.mox.StubOutWithMock(self.manager, 'get_key_pair')
        self.manager.get_key_pair(TEST_KEYPAIR_NAMES[0]).AndReturn(TEST_RETURN)
        self.manager.get_key_pair(TEST_KEYPAIR_NAMES[0]).AndReturn(None)

        self.mox.ReplayAll()

        self.assertTrue(self.manager.has_key_pair(TEST_KEYPAIR_NAMES[0]))
        self.assertFalse(self.manager.has_key_pair(TEST_KEYPAIR_NAMES[0]))

        self.mox.VerifyAll()

    def test_create_key_pair(self):
        conn_mock = self.stub_conn_mock()

        conn_mock.create_key_pair(
                TEST_KEYPAIR_NAMES[0]).AndReturn(TEST_RETURN)

        self.mox.ReplayAll()

        retval = self.manager.create_key_pair(TEST_KEYPAIR_NAMES[0])
        self.assertEqual(retval, TEST_RETURN)

        self.mox.VerifyAll()

    def test_delete_key_pair(self):
        conn_mock = self.stub_conn_mock()

        conn_mock.delete_key_pair(
                TEST_KEYPAIR_NAMES[0]).AndReturn(TEST_RETURN)

        self.mox.ReplayAll()

        retval = self.manager.delete_key_pair(TEST_KEYPAIR_NAMES[0])
        self.assertEqual(retval, None)

        self.mox.VerifyAll()

    def test_get_volumes(self):
        conn_mock = self.stub_conn_mock()

        conn_mock.get_all_volumes().AndReturn('testReturn')

        self.mox.ReplayAll()

        retval = self.manager.get_volumes()
        self.assertEqual(retval, TEST_RETURN)

        self.mox.VerifyAll()

    def test_create_volume(self):
        def mock_create_volume_params(size, d_name, d_descript, snapshot):
            return And(ContainsKeyValue('Size', size),
                       ContainsKeyValue('DisplayName', d_name),
                       ContainsKeyValue('DisplayDescription', d_descript))

        conn_mock = self.stub_conn_mock(count=2)

        params = mock_create_volume_params(TEST_SIZE, TEST_VOLUME_NAME,
                                           TEST_DESCRIPTION, TEST_SNAPSHOT)
        conn_mock.get_object('CreateVolume', params,
                             boto.ec2.volume.Volume).AndReturn(TEST_RETURN)

        params = mock_create_volume_params(TEST_SIZE, None, None, None)
        conn_mock.get_object('CreateVolume', params,
                             boto.ec2.volume.Volume).AndReturn(TEST_RETURN)

        self.mox.ReplayAll()

        retval = self.manager.create_volume(TEST_SIZE, TEST_VOLUME_NAME,
                                            TEST_DESCRIPTION, TEST_SNAPSHOT)
        self.assertEqual(retval, TEST_RETURN)

        retval = self.manager.create_volume(TEST_SIZE)
        self.assertEqual(retval, TEST_RETURN)

        self.mox.VerifyAll()

    def test_delete_volume(self):
        conn_mock = self.stub_conn_mock()

        conn_mock.delete_volume(TEST_VOLUME_ID).AndReturn(TEST_RETURN)

        self.mox.ReplayAll()

        retval = self.manager.delete_volume(TEST_VOLUME_ID)
        self.assertEqual(retval, TEST_RETURN)

        self.mox.VerifyAll()

    def test_attach_volume(self):
        TEST_DEVICE = 'testDevice'

        conn_mock = self.stub_conn_mock()

        conn_mock.attach_volume(TEST_VOLUME_ID, TEST_INSTANCE_ID,
                                TEST_DEVICE).AndReturn(TEST_RETURN)

        self.mox.ReplayAll()

        retval = self.manager.attach_volume(TEST_VOLUME_ID, TEST_INSTANCE_ID,
                                            TEST_DEVICE)
        self.assertEqual(retval, TEST_RETURN)

        self.mox.VerifyAll()

    def test_detach_volume(self):
        conn_mock = self.stub_conn_mock()

        conn_mock.detach_volume(TEST_VOLUME_ID).AndReturn(TEST_RETURN)

        self.mox.ReplayAll()

        retval = self.manager.detach_volume(TEST_VOLUME_ID)
        self.assertEqual(retval, TEST_RETURN)

        self.mox.VerifyAll()
