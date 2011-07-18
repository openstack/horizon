# vim: tabstop=4 shiftwidth=4 softtabstop=4

from django import http
from django import shortcuts
from django import test
from django.conf import settings
import mox

from django_openstack.middleware import keystone


def fake_render_to_response(template_name, context, context_instance=None,
                            mimetype='text/html'):
    """Replacement for render_to_response so that views can be tested
       without having to stub out templates that belong in the frontend
       implementation.

       Should be able to be tested using the django unit test assertions like a
       normal render_to_response return value can be.
    """
    class Template(object):
        def __init__(self, name):
            self.name = name

    if context_instance is None:
        context_instance = django_template.Context(context)
    else:
        context_instance.update(context)

    resp = http.HttpResponse()
    template = Template(template_name)

    resp.write('<html><body><p>'
               'This is a fake httpresponse for testing purposes only'
               '</p></body></html>')

    # Allows django.test.client to populate fields on the response object
    test.signals.template_rendered.send(template, template=template,
                                        context=context_instance)

    return resp


class TestCase(test.TestCase):
    TEST_PROJECT = 'test'
    TEST_REGION = 'test'
    TEST_STAFF_USER = 'staffUser'
    TEST_TENANT = 'aTenant'
    TEST_TOKEN = 'aToken'
    TEST_USER = 'test'

    TEST_SERVICE_CATALOG = {'cdn': [{'adminURL': 'http://cdn.admin-nets.local/v1.1/1234', 'region': 'RegionOne', 'internalURL': 'http://127.0.0.1:7777/v1.1/1234', 'publicURL': 'http://cdn.publicinternets.com/v1.1/1234'}], 'nova_compat': [{'adminURL': 'http://127.0.0.1:8774/v1.0', 'region': 'RegionOne', 'internalURL': 'http://localhost:8774/v1.0', 'publicURL': 'http://nova.publicinternets.com/v1.0/'}], 'nova': [{'adminURL': 'http://nova/novapi/admin', 'region': 'RegionOne', 'internalURL': 'http://nova/novapi/internal', 'publicURL': 'http://nova/novapi/public'}], 'keystone': [{'adminURL': 'http://127.0.0.1:8081/v2.0', 'region': 'RegionOne', 'internalURL': 'http://127.0.0.1:8080/v2.0', 'publicURL': 'http://keystone.publicinternets.com/v2.0'}], 'glance': [{'adminURL': 'http://glance/glanceapi/admin', 'region': 'RegionOne', 'internalURL': 'http://glance/glanceapi/internal', 'publicURL': 'http://glance/glanceapi/public'}], 'swift': [{'adminURL': 'http://swift.admin-nets.local:8080/', 'region': 'RegionOne', 'internalURL': 'http://127.0.0.1:8080/v1/AUTH_1234', 'publicURL': 'http://swift.publicinternets.com/v1/AUTH_1234'}]}

    def setUp(self):
        self.mox = mox.Mox()
        self._real_render_to_response = shortcuts.render_to_response
        shortcuts.render_to_response = fake_render_to_response

        self._real_get_user_from_request = keystone.get_user_from_request
        self.setActiveUser(self.TEST_TOKEN, self.TEST_USER, self.TEST_TENANT,
                           True, self.TEST_SERVICE_CATALOG)
        self.request = http.HttpRequest()
        keystone.AuthenticationMiddleware().process_request(self.request)

    def tearDown(self):
        self.mox.UnsetStubs()
        shortcuts.render_to_response = self._real_render_to_response
        keystone.get_user_from_request = self._real_get_user_from_request

    def assertRedirectsNoFollow(self, response, expected_url):
        self.assertEqual(response._headers['location'],
                         ('Location', settings.TESTSERVER + expected_url))
        self.assertEqual(response.status_code, 302)

    def setActiveUser(self, token, username, tenant, is_admin, service_catalog):
        keystone.get_user_from_request = \
                lambda x: keystone.User(token, username, tenant, is_admin, service_catalog)
