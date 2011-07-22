# vim: tabstop=4 shiftwidth=4 softtabstop=4

from django import http
from django import test
import mox

from django_openstack.middleware import keystone


class TestCase(test.TestCase):
    TEST_STAFF_USER = 'staffUser'
    TEST_TENANT = 'aTenant'
    TEST_TOKEN = 'aToken'
    TEST_USER = 'test'

    TEST_SERVICE_CATALOG = \
        {'cdn':
             [{'adminURL': 'http://cdn.admin-nets.local/v1.1/1234',
               'region': 'RegionOne',
               'internalURL': 'http://127.0.0.1:7777/v1.1/1234',
               'publicURL': 'http://cdn.publicinternets.com/v1.1/1234'}],
         'nova_compat':
             [{'adminURL': 'http://127.0.0.1:8774/v1.0',
               'region': 'RegionOne',
               'internalURL': 'http://localhost:8774/v1.0',
               'publicURL': 'http://nova.publicinternets.com/v1.0/'}],
         'nova':
             [{'adminURL': 'http://nova/novapi/admin',
               'region':'RegionOne',
               'internalURL': 'http://nova/novapi/internal',
               'publicURL': 'http://nova/novapi/public'}],
         'keystone':
             [{'adminURL': 'http://127.0.0.1:8081/v2.0',
               'region': 'RegionOne',
               'internalURL': 'http://127.0.0.1:8080/v2.0',
               'publicURL': 'http://keystone.publicinternets.com/v2.0'}],
         'glance':
             [{'adminURL': 'http://glance/glanceapi/admin',
               'region':'RegionOne',
               'internalURL': 'http://glance/glanceapi/internal',
               'publicURL': 'http://glance/glanceapi/public'}],
         'swift':
             [{'adminURL': 'http://swift.admin-nets.local:8080/',
               'region': 'RegionOne',
               'internalURL': 'http://127.0.0.1:8080/v1/AUTH_1234',
               'publicURL': 'http://swift.publicinternets.com/v1/AUTH_1234'}],
        }

    def setUp(self):
        self.mox = mox.Mox()

        self._real_get_user_from_request = keystone.get_user_from_request
        self.setActiveUser(self.TEST_TOKEN, self.TEST_USER, self.TEST_TENANT,
                           True, self.TEST_SERVICE_CATALOG)
        self.request = http.HttpRequest()
        keystone.AuthenticationMiddleware().process_request(self.request)

    def tearDown(self):
        self.mox.UnsetStubs()
        keystone.get_user_from_request = self._real_get_user_from_request

    def setActiveUser(self, token, username,
                      tenant, is_admin, service_catalog):
        keystone.get_user_from_request = \
                lambda x: keystone.User(token, username, tenant,
                                        is_admin, service_catalog)
