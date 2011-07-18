import datetime
import hashlib
import mox
import random

from django import test
from django.conf import settings
from django.db.models.signals import post_save
from django_openstack import models as nova_models
from django_openstack import utils
from django_openstack.core import connection
from nova_adminclient import NovaAdminClient


TEST_USER = 'testUser'
TEST_PROJECT = 'testProject'
TEST_AUTH_TOKEN = hashlib.sha1('').hexdigest()
TEST_AUTH_DATE = utils.utcnow()
TEST_BAD_AUTH_TOKEN = 'badToken'

HOUR = datetime.timedelta(seconds=3600)
AUTH_EXPIRATION_LENGTH = \
        datetime.timedelta(days=int(settings.CREDENTIAL_AUTHORIZATION_DAYS))


class CredentialsAuthorizationTests(test.TestCase):
    @classmethod
    def setUpClass(cls):
        # these post_save methods interact with external resources, shut them
        # down to test credentials
        post_save.disconnect(sender=nova_models.CredentialsAuthorization,
            dispatch_uid='django_openstack.CredentialsAuthorization.post_save')
        post_save.disconnect(sender=nova_models.CredentialsAuthorization,
                dispatch_uid='django_openstack.User.post_save')

    def setUp(self):
        test_cred = nova_models.CredentialsAuthorization()
        test_cred.username = TEST_USER
        test_cred.project = TEST_PROJECT
        test_cred.auth_date = TEST_AUTH_DATE
        test_cred.auth_token = TEST_AUTH_TOKEN
        test_cred.save()

        badTestCred = nova_models.CredentialsAuthorization()
        badTestCred.username = TEST_USER
        badTestCred.project = TEST_PROJECT
        badTestCred.auth_date = TEST_AUTH_DATE
        badTestCred.auth_token = TEST_BAD_AUTH_TOKEN
        badTestCred.save()

        self.mox = mox.Mox()

    def tearDown(self):
        self.mox.UnsetStubs()

    def test_get_by_token(self):
        TEST_MISSING_AUTH_TOKEN = hashlib.sha1('notAToken').hexdigest()

        # Token not a sha1, but exists in system
        cred = nova_models.CredentialsAuthorization.get_by_token(
                TEST_BAD_AUTH_TOKEN)
        self.assertTrue(cred is None)

        # Token doesn't exist
        cred = nova_models.CredentialsAuthorization.get_by_token(
                TEST_MISSING_AUTH_TOKEN)
        self.assertTrue(cred is None)

        # Good token
        cred = nova_models.CredentialsAuthorization.get_by_token(
                TEST_AUTH_TOKEN)
        self.assertTrue(cred is not None)

        # Expire the token
        cred.auth_date = utils.utcnow() - AUTH_EXPIRATION_LENGTH \
                                                 - HOUR
        cred.save()

        # Expired token
        cred = nova_models.CredentialsAuthorization.get_by_token(
                TEST_AUTH_TOKEN)
        self.assertTrue(cred is None)

    def test_authorize(self):
        TEST_USER2 = TEST_USER + '2'
        TEST_AUTH_TOKEN_2 = hashlib.sha1('token2').hexdigest()

        cred_class = nova_models.CredentialsAuthorization
        self.mox.StubOutWithMock(cred_class, 'create_auth_token')
        cred_class.create_auth_token(TEST_USER2).AndReturn(
                TEST_AUTH_TOKEN_2)

        self.mox.ReplayAll()

        cred = cred_class.authorize(TEST_USER2, TEST_PROJECT)

        self.mox.VerifyAll()

        self.assertTrue(cred is not None)
        self.assertEqual(cred.username, TEST_USER2)
        self.assertEqual(cred.project, TEST_PROJECT)
        self.assertEqual(cred.auth_token, TEST_AUTH_TOKEN_2)
        self.assertFalse(cred.auth_token_expired())

        cred = cred_class.get_by_token(TEST_AUTH_TOKEN_2)
        self.assertTrue(cred is not None)

    def test_create_auth_token(self):
        rand_state = random.getstate()
        expected_salt = hashlib.sha1(str(random.random())).hexdigest()[:5]
        expected_token = hashlib.sha1(expected_salt + TEST_USER).hexdigest()

        random.setstate(rand_state)
        auth_token = \
            nova_models.CredentialsAuthorization.create_auth_token(TEST_USER)
        self.assertEqual(expected_token, auth_token)

    def test_auth_token_expired(self):
        '''
        Test expired in past, expires in future, expires _right now_
        '''
        cred = \
            nova_models.CredentialsAuthorization.get_by_token(TEST_AUTH_TOKEN)

        cred.auth_date = utils.utcnow() - AUTH_EXPIRATION_LENGTH \
                                                 - HOUR
        self.assertTrue(cred.auth_token_expired())

        cred.auth_date = utils.utcnow()

        self.assertFalse(cred.auth_token_expired())

        # testing with time is tricky. Mock out "right now" test to avoid
        # timing issues
        time = utils.utcnow.override_time = utils.utcnow()
        cred.auth_date = time - AUTH_EXPIRATION_LENGTH

        self.assertTrue(cred.auth_token_expired())

        utils.utcnow.override_time = None

    def test_get_download_url(self):
        cred = \
            nova_models.CredentialsAuthorization.get_by_token(TEST_AUTH_TOKEN)

        expected_url = settings.CREDENTIAL_DOWNLOAD_URL + TEST_AUTH_TOKEN
        self.assertEqual(expected_url, cred.get_download_url())

    def test_get_zip(self):
        cred = \
            nova_models.CredentialsAuthorization.get_by_token(TEST_AUTH_TOKEN)

        admin_mock = self.mox.CreateMock(NovaAdminClient)

        self.mox.StubOutWithMock(connection, 'get_nova_admin_connection')
        connection.get_nova_admin_connection().AndReturn(admin_mock)

        admin_mock.get_zip(TEST_USER, TEST_PROJECT)

        self.mox.ReplayAll()

        cred.get_zip()

        self.mox.VerifyAll()

        cred = \
            nova_models.CredentialsAuthorization.get_by_token(TEST_AUTH_TOKEN)

        self.assertTrue(cred is None)
