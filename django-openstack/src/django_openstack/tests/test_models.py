from django import test
from django.conf import settings
from django_openstack import models as nova_models

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

    def test_create_auth_token(self):
        rand_state = random.getstate()
        expected_salt = hashlib.sha1(str(random.random())).hexdigest()[:5]
        expected_token = hashlib.sha1(expected_salt + TEST_USER).hexdigest()

        random.setstate(rand_state)
        auth_token = \
            nova_models.CredentialsAuthorization.create_auth_token(TEST_USER)
        self.assertEqual(expected_token, auth_token)

    def test_get_by_token(self):
        TEST_MISSING_AUTH_TOKEN = 'notAToken'

        cred = nova_models.CredentialsAuthorization.get_by_token(
                TEST_BAD_AUTH_TOKEN)

        self.assertTrue(cred is None)

        cred = nova_models.CredentialsAuthorization.get_by_token(
                TEST_MISSING_AUTH_TOKEN)

        self.assertTrue(cred is None)

        cred = nova_models.CredentialsAuthorization.get_by_token(
                TEST_AUTH_TOKEN)
        self.assertTrue(cred is not None)

        cred.auth_date = datetime.datetime.now() - AUTH_EXPIRATION_LENGTH \
                                                 - HOUR
        cred.save()

        cred = nova_models.CredentialsAuthorization.get_by_token(
                TEST_AUTH_TOKEN)

        self.assertTrue(cred is None)


    def test_auth_token_expired(self):
        '''
        Test expired in past, expires in future, expires in future
        '''
        cred = \
            nova_models.CredentialsAuthorization.get_by_token(TEST_AUTH_TOKEN)
        self.assertTrue(cred is not None)

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
        cred.datetime.datetime.AndReturn(datetime_mox)

        self.assertTrue(cred.auth_token_expired())
