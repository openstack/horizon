from django import test
from django.conf import settings
from django_openstack import models as nova_models
from django_openstack.core import connection
from nova_adminclient import NovaAdminClient

import datetime
import hashlib
import mox
import random


TEST_USER = 'testUser'
TEST_PROJECT = 'testProject'
TEST_AUTH_TOKEN = hashlib.sha1('').hexdigest()
TEST_AUTH_DATE = datetime.datetime.now()
TEST_BAD_AUTH_TOKEN = 'badToken'

HOUR = datetime.timedelta(seconds=3600)
AUTH_EXPIRATION_LENGTH = \
        datetime.timedelta(days=int(settings.CREDENTIAL_AUTHORIZATION_DAYS))


class CredentialsAuthorizationTests(test.TestCase):
    def setUp(self):
        testCred = nova_models.CredentialsAuthorization()
        testCred.username = TEST_USER
        testCred.project = TEST_PROJECT
        testCred.auth_date = TEST_AUTH_DATE
        testCred.auth_token = TEST_AUTH_TOKEN
        testCred.save()

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
        cred.auth_date = datetime.datetime.now() - AUTH_EXPIRATION_LENGTH \
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
        self.assertTrue(cred.username == TEST_USER2)
        self.assertTrue(cred.project == TEST_PROJECT)
        self.assertTrue(cred.auth_token == TEST_AUTH_TOKEN_2)
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

        cred.auth_date = datetime.datetime.now() - AUTH_EXPIRATION_LENGTH \
                                                 - HOUR
        self.assertTrue(cred.auth_token_expired())

        cred.auth_date = datetime.datetime.now()

        self.assertFalse(cred.auth_token_expired())

        # testing with time is tricky. Mock out "right now" test to avoid
        # timing issues
        time = datetime.datetime.now()
        cred.auth_date = time - AUTH_EXPIRATION_LENGTH

        datetime_mox = self.mox.CreateMockAnything()
        self.mox.StubOutWithMock(datetime_mox, 'datetime')
        datetime_mox.datetime.now.AndReturn(time)

        cred.datetime = datetime_mox

        self.mox.ReplayAll()

        self.assertTrue(cred.auth_token_expired())

        self.mox.VerifyAll()

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
