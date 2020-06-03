# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
# implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import uuid

from django.conf import settings
from django.contrib import auth
from django import test
from django.test.utils import override_settings
from django.urls import reverse
from keystoneauth1 import exceptions as keystone_exceptions
from keystoneauth1.identity import v3 as v3_auth
from keystoneauth1 import session
from keystoneauth1 import token_endpoint
from keystoneclient.v3 import client as client_v3
from mox3 import mox
from testscenarios import load_tests_apply_scenarios

from openstack_auth.tests import data_v3
from openstack_auth import utils


DEFAULT_DOMAIN = settings.OPENSTACK_KEYSTONE_DEFAULT_DOMAIN


class OpenStackAuthTestsMixin(object):
    '''Common functions for version specific tests.'''

    scenarios = [
        ('pure', {'interface': None}),
        ('public', {'interface': 'publicURL'}),
        ('internal', {'interface': 'internalURL'}),
        ('admin', {'interface': 'adminURL'})
    ]

    def _mock_unscoped_client(self, user):
        plugin = self._create_password_auth()
        plugin.get_access(mox.IsA(session.Session)). \
            AndReturn(self.data.unscoped_access_info)
        plugin.auth_url = settings.OPENSTACK_KEYSTONE_URL
        return self.ks_client_module.Client(session=mox.IsA(session.Session),
                                            auth=plugin)

    def _mock_unscoped_client_with_token(self, user, unscoped):
        plugin = token_endpoint.Token(settings.OPENSTACK_KEYSTONE_URL,
                                      unscoped.auth_token)
        return self.ks_client_module.Client(session=mox.IsA(session.Session),
                                            auth=plugin)

    def _mock_client_token_auth_failure(self, unscoped, tenant_id):
        plugin = self._create_token_auth(tenant_id, unscoped.auth_token)
        plugin.get_access(mox.IsA(session.Session)). \
            AndRaise(keystone_exceptions.AuthorizationFailure)

    def _mock_client_password_auth_failure(self, username, password, exc):
        plugin = self._create_password_auth(username=username,
                                            password=password)
        plugin.get_access(mox.IsA(session.Session)).AndRaise(exc)

    def _mock_scoped_client_for_tenant(self, auth_ref, tenant_id, url=None,
                                       client=True, token=None):
        if url is None:
            url = settings.OPENSTACK_KEYSTONE_URL

        if not token:
            token = self.data.unscoped_access_info.auth_token

        plugin = self._create_token_auth(
            tenant_id,
            token=token,
            url=url)
        self.scoped_token_auth = plugin
        plugin.get_access(mox.IsA(session.Session)).AndReturn(auth_ref)
        if client:
            return self.ks_client_module.Client(
                session=mox.IsA(session.Session),
                auth=plugin)

    def get_form_data(self, user):
        return {'region': "default",
                'domain': DEFAULT_DOMAIN,
                'password': user.password,
                'username': user.name}


class OpenStackAuthFederatedTestsMixin(object):
    """Common functions for federation"""
    def _mock_unscoped_federated_list_projects(self, client, projects):
        client.federation = self.mox.CreateMockAnything()
        client.federation.projects = self.mox.CreateMockAnything()
        client.federation.projects.list().AndReturn(projects)

    def _mock_unscoped_list_domains(self, client, domains):
        client.auth = self.mox.CreateMockAnything()
        client.auth.domains().AndReturn(domains)

    def _mock_unscoped_token_client(self, unscoped, auth_url=None,
                                    client=True, plugin=None):
        if not auth_url:
            auth_url = settings.OPENSTACK_KEYSTONE_URL
        if unscoped and not plugin:
            plugin = self._create_token_auth(
                None,
                token=unscoped.auth_token,
                url=auth_url)
            plugin.get_access(mox.IsA(session.Session)).AndReturn(unscoped)
        plugin.auth_url = auth_url
        if client:
            return self.ks_client_module.Client(
                session=mox.IsA(session.Session),
                auth=plugin)

    def _mock_plugin(self, unscoped, auth_url=None):
        if not auth_url:
            auth_url = settings.OPENSTACK_KEYSTONE_URL
        plugin = self._create_token_auth(
            None,
            token=unscoped.auth_token,
            url=auth_url)
        plugin.get_access(mox.IsA(session.Session)).AndReturn(unscoped)
        plugin.auth_url = settings.OPENSTACK_KEYSTONE_URL
        return plugin

    def _mock_federated_client_list_projects(self, unscoped_auth, projects):
        client = self._mock_unscoped_token_client(None, plugin=unscoped_auth)
        self._mock_unscoped_federated_list_projects(client, projects)

    def _mock_federated_client_list_domains(self, unscoped_auth, domains):
        client = self._mock_unscoped_token_client(None, plugin=unscoped_auth)
        self._mock_unscoped_list_domains(client, domains)


class OpenStackAuthTestsV3(OpenStackAuthTestsMixin,
                           OpenStackAuthFederatedTestsMixin,
                           test.TestCase):

    def _mock_unscoped_client_list_projects(self, user, projects):
        client = self._mock_unscoped_client(user)
        self._mock_unscoped_list_projects(client, user, projects)

    def _mock_unscoped_list_projects(self, client, user, projects):
        client.projects = self.mox.CreateMockAnything()
        client.projects.list(user=user.id).AndReturn(projects)

    def _mock_unscoped_client_list_projects_fail(self, user):
        client = self._mock_unscoped_client(user)
        self._mock_unscoped_list_projects_fail(client, user)

    def _mock_unscoped_list_projects_fail(self, client, user):
        plugin = self._create_token_auth(
            project_id=None,
            domain_name=DEFAULT_DOMAIN,
            token=self.data.unscoped_access_info.auth_token,
            url=settings.OPENSTACK_KEYSTONE_URL)
        plugin.get_access(mox.IsA(session.Session)).AndReturn(
            self.data.domain_scoped_access_info)
        client.projects = self.mox.CreateMockAnything()
        client.projects.list(user=user.id).AndRaise(
            keystone_exceptions.AuthorizationFailure)

    def _mock_unscoped_and_domain_list_projects(self, user, projects):
        client = self._mock_unscoped_client(user)
        self._mock_scoped_for_domain(projects)
        self._mock_unscoped_list_projects(client, user, projects)

    def _mock_scoped_for_domain(self, projects):
        url = settings.OPENSTACK_KEYSTONE_URL

        plugin = self._create_token_auth(
            project_id=None,
            domain_name=DEFAULT_DOMAIN,
            token=self.data.unscoped_access_info.auth_token,
            url=url)

        plugin.get_access(mox.IsA(session.Session)).AndReturn(
            self.data.domain_scoped_access_info)

        # if no projects or no enabled projects for user, but domain scoped
        # token client auth gets set to domain scoped auth otherwise it's set
        # to the project scoped auth and that happens in a different mock
        enabled_projects = [project for project in projects if project.enabled]
        if not projects or not enabled_projects:
            return self.ks_client_module.Client(
                session=mox.IsA(session.Session),
                auth=plugin)

    def _create_password_auth(self, username=None, password=None, url=None):
        if not username:
            username = self.data.user.name

        if not password:
            password = self.data.user.password

        if not url:
            url = settings.OPENSTACK_KEYSTONE_URL

        return v3_auth.Password(auth_url=url,
                                password=password,
                                username=username,
                                user_domain_name=DEFAULT_DOMAIN,
                                unscoped=True)

    def _create_token_auth(self, project_id, token=None, url=None,
                           domain_name=None):
        if not token:
            token = self.data.unscoped_access_info.auth_token

        if not url:
            url = settings.OPENSTACK_KEYSTONE_URL

        if domain_name:
            return v3_auth.Token(auth_url=url,
                                 token=token,
                                 domain_name=domain_name,
                                 reauthenticate=False)
        else:
            return v3_auth.Token(auth_url=url,
                                 token=token,
                                 project_id=project_id,
                                 reauthenticate=False)

    def setUp(self):
        super(OpenStackAuthTestsV3, self).setUp()

        if getattr(self, 'interface', None):
            override = self.settings(OPENSTACK_ENDPOINT_TYPE=self.interface)
            override.enable()
            self.addCleanup(override.disable)

        self.mox = mox.Mox()
        self.addCleanup(self.mox.VerifyAll)
        self.addCleanup(self.mox.UnsetStubs)

        self.data = data_v3.generate_test_data()
        self.ks_client_module = client_v3
        settings.OPENSTACK_API_VERSIONS['identity'] = 3
        settings.OPENSTACK_KEYSTONE_URL = "http://localhost:5000/v3"

        self.mox.StubOutClassWithMocks(token_endpoint, 'Token')
        self.mox.StubOutClassWithMocks(v3_auth, 'Token')
        self.mox.StubOutClassWithMocks(v3_auth, 'Password')
        self.mox.StubOutClassWithMocks(client_v3, 'Client')
        self.mox.StubOutClassWithMocks(v3_auth, 'Keystone2Keystone')

    def test_login(self):
        projects = [self.data.project_one, self.data.project_two]
        user = self.data.user
        unscoped = self.data.unscoped_access_info

        form_data = self.get_form_data(user)
        self._mock_unscoped_and_domain_list_projects(user, projects)
        self._mock_scoped_client_for_tenant(unscoped, self.data.project_one.id)

        self.mox.ReplayAll()

        url = reverse('login')

        # GET the page to set the test cookie.
        response = self.client.get(url, form_data)
        self.assertEqual(response.status_code, 200)

        # POST to the page to log in.
        response = self.client.post(url, form_data)
        self.assertRedirects(response, settings.LOGIN_REDIRECT_URL)

    def test_login_with_disabled_project(self):
        # Test to validate that authentication will not try to get
        # scoped token for disabled project.
        projects = [self.data.project_two, self.data.project_one]
        user = self.data.user
        unscoped = self.data.unscoped_access_info

        form_data = self.get_form_data(user)
        self._mock_unscoped_and_domain_list_projects(user, projects)
        self._mock_scoped_client_for_tenant(unscoped, self.data.project_one.id)
        self.mox.ReplayAll()

        url = reverse('login')

        # GET the page to set the test cookie.
        response = self.client.get(url, form_data)
        self.assertEqual(response.status_code, 200)

        # POST to the page to log in.
        response = self.client.post(url, form_data)
        self.assertRedirects(response, settings.LOGIN_REDIRECT_URL)

    def test_no_enabled_projects(self):
        projects = [self.data.project_two]
        user = self.data.user

        form_data = self.get_form_data(user)

        self._mock_unscoped_and_domain_list_projects(user, projects)
        self.mox.ReplayAll()

        url = reverse('login')

        # GET the page to set the test cookie.
        response = self.client.get(url, form_data)
        self.assertEqual(response.status_code, 200)

        # POST to the page to log in.
        response = self.client.post(url, form_data)
        self.assertRedirects(response, settings.LOGIN_REDIRECT_URL)

    def test_no_projects(self):
        user = self.data.user
        form_data = self.get_form_data(user)

        self._mock_unscoped_and_domain_list_projects(user, [])
        self.mox.ReplayAll()

        url = reverse('login')

        # GET the page to set the test cookie.
        response = self.client.get(url, form_data)
        self.assertEqual(response.status_code, 200)

        # POST to the page to log in.
        response = self.client.post(url, form_data)
        self.assertRedirects(response, settings.LOGIN_REDIRECT_URL)

    def test_fail_projects(self):
        user = self.data.user

        form_data = self.get_form_data(user)
        self._mock_unscoped_client_list_projects_fail(user)
        self.mox.ReplayAll()

        url = reverse('login')

        # GET the page to set the test cookie.
        response = self.client.get(url, form_data)
        self.assertEqual(response.status_code, 200)

        # POST to the page to log in.
        response = self.client.post(url, form_data)
        self.assertTemplateUsed(response, 'auth/login.html')
        self.assertContains(response,
                            'Unable to retrieve authorized projects.')

    def test_invalid_credentials(self):
        user = self.data.user

        form_data = self.get_form_data(user)

        form_data['password'] = "invalid"

        exc = keystone_exceptions.Unauthorized(401)
        self._mock_client_password_auth_failure(user.name, "invalid", exc)

        self.mox.ReplayAll()

        url = reverse('login')

        # GET the page to set the test cookie.
        response = self.client.get(url, form_data)
        self.assertEqual(response.status_code, 200)

        # POST to the page to log in.
        response = self.client.post(url, form_data)
        self.assertTemplateUsed(response, 'auth/login.html')
        self.assertContains(response, "Invalid credentials.")

    def test_exception(self):
        user = self.data.user
        form_data = self.get_form_data(user)
        exc = keystone_exceptions.ClientException('error 500')
        self._mock_client_password_auth_failure(user.name, user.password, exc)
        self.mox.ReplayAll()

        url = reverse('login')

        # GET the page to set the test cookie.
        response = self.client.get(url, form_data)
        self.assertEqual(response.status_code, 200)

        # POST to the page to log in.
        response = self.client.post(url, form_data)

        self.assertTemplateUsed(response, 'auth/login.html')
        self.assertContains(response,
                            ("An error occurred authenticating. Please try "
                             "again later."))

    def test_switch(self, next=None):
        project = self.data.project_two
        projects = [self.data.project_one, self.data.project_two]
        user = self.data.user
        scoped = self.data.scoped_access_info
        sc = self.data.service_catalog
        et = getattr(settings, 'OPENSTACK_ENDPOINT_TYPE', 'publicURL')

        form_data = self.get_form_data(user)

        self._mock_unscoped_and_domain_list_projects(user, projects)
        self._mock_scoped_client_for_tenant(scoped, self.data.project_one.id)
        self._mock_scoped_client_for_tenant(
            scoped,
            project.id,
            url=sc.url_for(service_type='identity', interface=et),
            client=False)

        self.mox.ReplayAll()

        url = reverse('login')

        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

        response = self.client.post(url, form_data)
        self.assertRedirects(response, settings.LOGIN_REDIRECT_URL)

        url = reverse('switch_tenants', args=[project.id])

        scoped._project['id'] = self.data.project_two.id

        if next:
            form_data.update({auth.REDIRECT_FIELD_NAME: next})

        response = self.client.get(url, form_data)

        if next:
            expected_url = next
            self.assertEqual(response['location'], expected_url)
        else:
            self.assertRedirects(response, settings.LOGIN_REDIRECT_URL)

        self.assertEqual(self.client.session['token'].project['id'],
                         scoped.project_id)

    def test_switch_with_next(self):
        self.test_switch(next='/next_url')

    def test_switch_region(self, next=None):
        projects = [self.data.project_one, self.data.project_two]
        user = self.data.user
        scoped = self.data.unscoped_access_info
        sc = self.data.service_catalog

        form_data = self.get_form_data(user)
        self._mock_unscoped_and_domain_list_projects(user, projects)
        self._mock_scoped_client_for_tenant(scoped, self.data.project_one.id)

        self.mox.ReplayAll()

        url = reverse('login')

        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

        response = self.client.post(url, form_data)
        self.assertRedirects(response, settings.LOGIN_REDIRECT_URL)

        old_region = sc.get_endpoints()['compute'][0]['region']
        self.assertEqual(self.client.session['services_region'], old_region)

        region = sc.get_endpoints()['compute'][1]['region']
        url = reverse('switch_services_region', args=[region])

        form_data['region_name'] = region

        if next:
            form_data.update({auth.REDIRECT_FIELD_NAME: next})

        response = self.client.get(url, form_data)

        if next:
            expected_url = next
            self.assertEqual(response['location'], expected_url)
        else:
            self.assertRedirects(response, settings.LOGIN_REDIRECT_URL)

        self.assertEqual(self.client.session['services_region'], region)

    def test_switch_region_with_next(self, next=None):
        self.test_switch_region(next='/next_url')

    def test_switch_keystone_provider_remote_fail(self):
        auth_url = settings.OPENSTACK_KEYSTONE_URL
        target_provider = 'k2kserviceprovider'
        self.data = data_v3.generate_test_data(service_providers=True)
        self.sp_data = data_v3.generate_test_data(endpoint='http://sp2')
        projects = [self.data.project_one, self.data.project_two]
        user = self.data.user
        unscoped = self.data.unscoped_access_info
        form_data = self.get_form_data(user)

        # mock authenticate
        self._mock_unscoped_and_domain_list_projects(user, projects)
        self._mock_scoped_client_for_tenant(unscoped, self.data.project_one.id)

        # mock switch
        plugin = v3_auth.Token(auth_url=auth_url,
                               token=unscoped.auth_token,
                               project_id=None,
                               reauthenticate=False)
        plugin.get_access(mox.IsA(session.Session)
                          ).AndReturn(self.data.unscoped_access_info)
        plugin.auth_url = auth_url
        client = self.ks_client_module.Client(session=mox.IsA(session.Session),
                                              auth=plugin)

        self._mock_unscoped_list_projects(client, user, projects)
        plugin = self._create_token_auth(
            self.data.project_one.id,
            token=self.data.unscoped_access_info.auth_token,
            url=settings.OPENSTACK_KEYSTONE_URL)
        plugin.get_access(mox.IsA(session.Session)).AndReturn(
            settings.OPENSTACK_KEYSTONE_URL)
        plugin.get_sp_auth_url(
            mox.IsA(session.Session), target_provider
        ).AndReturn('https://k2kserviceprovider/sp_url')

        # let the K2K plugin fail when logging in
        plugin = v3_auth.Keystone2Keystone(
            base_plugin=plugin, service_provider=target_provider)
        plugin.get_access(mox.IsA(session.Session)).AndRaise(
            keystone_exceptions.AuthorizationFailure)
        self.mox.ReplayAll()

        # Log in
        url = reverse('login')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

        response = self.client.post(url, form_data)
        self.assertRedirects(response, settings.LOGIN_REDIRECT_URL)

        # Switch
        url = reverse('switch_keystone_provider', args=[target_provider])
        form_data['keystone_provider'] = target_provider
        response = self.client.get(url, form_data, follow=True)
        self.assertRedirects(response, settings.LOGIN_REDIRECT_URL)

        # Assert that provider has not changed because of failure
        self.assertEqual(self.client.session['keystone_provider_id'],
                         'localkeystone')
        # These should never change
        self.assertEqual(self.client.session['k2k_base_unscoped_token'],
                         unscoped.auth_token)
        self.assertEqual(self.client.session['k2k_auth_url'], auth_url)

    def test_switch_keystone_provider_remote(self):
        auth_url = settings.OPENSTACK_KEYSTONE_URL
        target_provider = 'k2kserviceprovider'
        self.data = data_v3.generate_test_data(service_providers=True)
        self.sp_data = data_v3.generate_test_data(endpoint='http://sp2')
        projects = [self.data.project_one, self.data.project_two]
        domains = []
        user = self.data.user
        unscoped = self.data.unscoped_access_info
        form_data = self.get_form_data(user)

        # mock authenticate
        self._mock_unscoped_and_domain_list_projects(user, projects)
        self._mock_scoped_client_for_tenant(unscoped, self.data.project_one.id)

        # mock switch
        plugin = v3_auth.Token(auth_url=auth_url,
                               token=unscoped.auth_token,
                               project_id=None,
                               reauthenticate=False)
        plugin.get_access(mox.IsA(session.Session)).AndReturn(
            self.data.unscoped_access_info)

        plugin.auth_url = auth_url
        client = self.ks_client_module.Client(session=mox.IsA(session.Session),
                                              auth=plugin)

        self._mock_unscoped_list_projects(client, user, projects)
        plugin = self._create_token_auth(
            self.data.project_one.id,
            token=self.data.unscoped_access_info.auth_token,
            url=settings.OPENSTACK_KEYSTONE_URL)
        plugin.get_access(mox.IsA(session.Session)).AndReturn(
            settings.OPENSTACK_KEYSTONE_URL)

        plugin.get_sp_auth_url(
            mox.IsA(session.Session), target_provider
        ).AndReturn('https://k2kserviceprovider/sp_url')
        plugin = v3_auth.Keystone2Keystone(base_plugin=plugin,
                                           service_provider=target_provider)
        plugin.get_access(mox.IsA(session.Session)). \
            AndReturn(self.sp_data.unscoped_access_info)
        plugin.auth_url = 'http://service_provider_endp:5000/v3'

        # mock authenticate for service provider
        sp_projects = [self.sp_data.project_one, self.sp_data.project_two]
        sp_unscoped = self.sp_data.federated_unscoped_access_info
        sp_unscoped_auth = self._mock_plugin(sp_unscoped,
                                             auth_url=plugin.auth_url)
        client = self._mock_unscoped_token_client(None, plugin.auth_url,
                                                  plugin=sp_unscoped_auth)
        self._mock_unscoped_list_domains(client, domains)
        client = self._mock_unscoped_token_client(None, plugin.auth_url,
                                                  plugin=sp_unscoped_auth)
        self._mock_unscoped_federated_list_projects(client, sp_projects)
        self._mock_scoped_client_for_tenant(sp_unscoped,
                                            self.sp_data.project_one.id,
                                            url=plugin.auth_url,
                                            token=sp_unscoped.auth_token)

        self.mox.ReplayAll()

        # Log in
        url = reverse('login')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

        response = self.client.post(url, form_data)
        self.assertRedirects(response, settings.LOGIN_REDIRECT_URL)

        # Switch
        url = reverse('switch_keystone_provider', args=[target_provider])
        form_data['keystone_provider'] = target_provider
        response = self.client.get(url, form_data, follow=True)
        self.assertRedirects(response, settings.LOGIN_REDIRECT_URL)

        # Assert keystone provider has changed
        self.assertEqual(self.client.session['keystone_provider_id'],
                         target_provider)
        # These should not change
        self.assertEqual(self.client.session['k2k_base_unscoped_token'],
                         unscoped.auth_token)
        self.assertEqual(self.client.session['k2k_auth_url'], auth_url)

    def test_switch_keystone_provider_local(self):
        auth_url = settings.OPENSTACK_KEYSTONE_URL
        self.data = data_v3.generate_test_data(service_providers=True)
        keystone_provider = 'localkeystone'
        projects = [self.data.project_one, self.data.project_two]
        domains = []
        user = self.data.user
        unscoped = self.data.unscoped_access_info
        form_data = self.get_form_data(user)

        # mock authenticate
        self._mock_unscoped_and_domain_list_projects(user, projects)
        self._mock_scoped_client_for_tenant(unscoped, self.data.project_one.id)
        self._mock_unscoped_token_client(unscoped,
                                         auth_url=auth_url,
                                         client=False)
        unscoped_auth = self._mock_plugin(unscoped)
        client = self._mock_unscoped_token_client(None, auth_url=auth_url,
                                                  plugin=unscoped_auth)
        self._mock_unscoped_list_domains(client, domains)
        client = self._mock_unscoped_token_client(None, auth_url=auth_url,
                                                  plugin=unscoped_auth)
        self._mock_unscoped_list_projects(client, user, projects)
        self._mock_scoped_client_for_tenant(unscoped, self.data.project_one.id)

        self.mox.ReplayAll()

        # Log in
        url = reverse('login')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

        response = self.client.post(url, form_data)
        self.assertRedirects(response, settings.LOGIN_REDIRECT_URL)

        # Switch
        url = reverse('switch_keystone_provider', args=[keystone_provider])
        form_data['keystone_provider'] = keystone_provider
        response = self.client.get(url, form_data, follow=True)
        self.assertRedirects(response, settings.LOGIN_REDIRECT_URL)

        # Assert nothing has changed since we are going from local to local
        self.assertEqual(self.client.session['keystone_provider_id'],
                         keystone_provider)
        self.assertEqual(self.client.session['k2k_base_unscoped_token'],
                         unscoped.auth_token)
        self.assertEqual(self.client.session['k2k_auth_url'], auth_url)

    def test_switch_keystone_provider_local_fail(self):
        auth_url = settings.OPENSTACK_KEYSTONE_URL
        self.data = data_v3.generate_test_data(service_providers=True)
        keystone_provider = 'localkeystone'
        projects = [self.data.project_one, self.data.project_two]
        user = self.data.user
        unscoped = self.data.unscoped_access_info
        form_data = self.get_form_data(user)

        # mock authenticate
        self._mock_unscoped_and_domain_list_projects(user, projects)
        self._mock_scoped_client_for_tenant(unscoped, self.data.project_one.id)

        # Let using the base token for logging in fail
        plugin = v3_auth.Token(auth_url=auth_url,
                               token=unscoped.auth_token,
                               project_id=None,
                               reauthenticate=False)
        plugin.get_access(mox.IsA(session.Session)). \
            AndRaise(keystone_exceptions.AuthorizationFailure)
        plugin.auth_url = auth_url
        self.mox.ReplayAll()

        # Log in
        url = reverse('login')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

        response = self.client.post(url, form_data)
        self.assertRedirects(response, settings.LOGIN_REDIRECT_URL)

        # Switch
        url = reverse('switch_keystone_provider', args=[keystone_provider])
        form_data['keystone_provider'] = keystone_provider
        response = self.client.get(url, form_data, follow=True)
        self.assertRedirects(response, settings.LOGIN_REDIRECT_URL)

        # Assert
        self.assertEqual(self.client.session['keystone_provider_id'],
                         keystone_provider)
        self.assertEqual(self.client.session['k2k_base_unscoped_token'],
                         unscoped.auth_token)
        self.assertEqual(self.client.session['k2k_auth_url'], auth_url)

    def test_tenant_sorting(self):
        projects = [self.data.project_two, self.data.project_one]
        expected_projects = [self.data.project_one, self.data.project_two]
        user = self.data.user
        unscoped = self.data.unscoped_access_info

        client = self._mock_unscoped_client_with_token(user, unscoped)
        self._mock_unscoped_list_projects(client, user, projects)
        self.mox.ReplayAll()

        project_list = utils.get_project_list(
            user_id=user.id,
            auth_url=settings.OPENSTACK_KEYSTONE_URL,
            token=unscoped.auth_token)
        self.assertEqual(project_list, expected_projects)

    def test_login_form_multidomain(self):
        override = self.settings(OPENSTACK_KEYSTONE_MULTIDOMAIN_SUPPORT=True)
        override.enable()
        self.addCleanup(override.disable)

        url = reverse('login')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'id="id_domain"')
        self.assertContains(response, 'name="domain"')

    def test_login_form_multidomain_dropdown(self):
        override = self.settings(OPENSTACK_KEYSTONE_MULTIDOMAIN_SUPPORT=True,
                                 OPENSTACK_KEYSTONE_DOMAIN_DROPDOWN=True,
                                 OPENSTACK_KEYSTONE_DOMAIN_CHOICES=(
                                     ('Default', 'Default'),)
                                 )
        override.enable()
        self.addCleanup(override.disable)

        url = reverse('login')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'id="id_domain"')
        self.assertContains(response, 'name="domain"')
        self.assertContains(response, 'option value="Default"')
        settings.OPENSTACK_KEYSTONE_DOMAIN_DROPDOWN = False

    def test_password_expired(self):
        user = self.data.user
        form_data = self.get_form_data(user)

        class ExpiredException(keystone_exceptions.Unauthorized):
            http_status = 401
            message = ("The password is expired and needs to be changed"
                       " for user: %s." % user.id)

        exc = ExpiredException()
        self._mock_client_password_auth_failure(user.name, user.password, exc)
        self.mox.ReplayAll()

        url = reverse('login')

        # GET the page to set the test cookie.
        response = self.client.get(url, form_data)
        self.assertEqual(response.status_code, 200)

        # POST to the page to log in.
        response = self.client.post(url, form_data)

        # This fails with TemplateDoesNotExist for some reason.
        # self.assertRedirects(response, reverse('password', args=[user.id]))
        # so instead we check for the redirect manually:

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, "/password/%s/" % user.id)


class OpenStackAuthTestsWebSSO(OpenStackAuthTestsMixin,
                               OpenStackAuthFederatedTestsMixin,
                               test.TestCase):

    def _create_token_auth(self, project_id=None, token=None, url=None):
        if not token:
            token = self.data.federated_unscoped_access_info.auth_token

        if not url:
            url = settings.OPENSTACK_KEYSTONE_URL

        return v3_auth.Token(auth_url=url,
                             token=token,
                             project_id=project_id,
                             reauthenticate=False)

    def setUp(self):
        super(OpenStackAuthTestsWebSSO, self).setUp()

        self.mox = mox.Mox()
        self.addCleanup(self.mox.VerifyAll)
        self.addCleanup(self.mox.UnsetStubs)

        self.data = data_v3.generate_test_data()
        self.ks_client_module = client_v3

        self.idp_id = uuid.uuid4().hex
        self.idp_oidc_id = uuid.uuid4().hex
        self.idp_saml2_id = uuid.uuid4().hex

        settings.OPENSTACK_API_VERSIONS['identity'] = 3
        settings.OPENSTACK_KEYSTONE_URL = 'http://localhost:5000/v3'
        settings.WEBSSO_ENABLED = True
        settings.WEBSSO_CHOICES = (
            ('credentials', 'Keystone Credentials'),
            ('oidc', 'OpenID Connect'),
            ('saml2', 'Security Assertion Markup Language'),
            (self.idp_oidc_id, 'IDP OIDC'),
            (self.idp_saml2_id, 'IDP SAML2')
        )
        settings.WEBSSO_IDP_MAPPING = {
            self.idp_oidc_id: (self.idp_id, 'oidc'),
            self.idp_saml2_id: (self.idp_id, 'saml2')
        }

        self.mox.StubOutClassWithMocks(token_endpoint, 'Token')
        self.mox.StubOutClassWithMocks(v3_auth, 'Token')
        self.mox.StubOutClassWithMocks(v3_auth, 'Password')
        self.mox.StubOutClassWithMocks(client_v3, 'Client')

    def test_login_form(self):
        url = reverse('login')

        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'credentials')
        self.assertContains(response, 'oidc')
        self.assertContains(response, 'saml2')
        self.assertContains(response, self.idp_oidc_id)
        self.assertContains(response, self.idp_saml2_id)

    def test_websso_redirect_by_protocol(self):
        origin = 'http://testserver/auth/websso/'
        protocol = 'oidc'
        redirect_url = ('%s/auth/OS-FEDERATION/websso/%s?origin=%s' %
                        (settings.OPENSTACK_KEYSTONE_URL, protocol, origin))

        form_data = {'auth_type': protocol,
                     'region': 'default'}
        url = reverse('login')

        # POST to the page and redirect to keystone.
        response = self.client.post(url, form_data)
        self.assertRedirects(response, redirect_url, status_code=302,
                             target_status_code=404)

    def test_websso_redirect_by_idp(self):
        origin = 'http://testserver/auth/websso/'
        protocol = 'oidc'
        redirect_url = ('%s/auth/OS-FEDERATION/identity_providers/%s'
                        '/protocols/%s/websso?origin=%s' %
                        (settings.OPENSTACK_KEYSTONE_URL, self.idp_id,
                         protocol, origin))

        form_data = {'auth_type': self.idp_oidc_id,
                     'region': 'default'}
        url = reverse('login')

        # POST to the page and redirect to keystone.
        response = self.client.post(url, form_data)
        self.assertRedirects(response, redirect_url, status_code=302,
                             target_status_code=404)

    @override_settings(WEBSSO_KEYSTONE_URL='http://keystone-public:5000/v3')
    def test_websso_redirect_using_websso_keystone_url(self):
        origin = 'http://testserver/auth/websso/'
        protocol = 'oidc'
        redirect_url = ('%s/auth/OS-FEDERATION/identity_providers/%s'
                        '/protocols/%s/websso?origin=%s' %
                        (settings.WEBSSO_KEYSTONE_URL, self.idp_id,
                         protocol, origin))

        form_data = {'auth_type': self.idp_oidc_id,
                     'region': 'default'}
        url = reverse('login')

        # POST to the page and redirect to keystone.
        response = self.client.post(url, form_data)
        # verify that the request was sent back to WEBSSO_KEYSTONE_URL
        self.assertRedirects(response, redirect_url, status_code=302,
                             target_status_code=404)

    def test_websso_login(self):
        projects = [self.data.project_one, self.data.project_two]
        domains = []
        unscoped = self.data.federated_unscoped_access_info
        token = unscoped.auth_token
        unscoped_auth = self._mock_plugin(unscoped)

        form_data = {'token': token}
        self._mock_federated_client_list_domains(unscoped_auth, domains)
        self._mock_federated_client_list_projects(unscoped_auth, projects)
        self._mock_scoped_client_for_tenant(unscoped, self.data.project_one.id)

        self.mox.ReplayAll()

        url = reverse('websso')

        # POST to the page to log in.
        response = self.client.post(url, form_data)
        self.assertRedirects(response, settings.LOGIN_REDIRECT_URL)

    def test_websso_login_with_auth_in_url(self):
        settings.OPENSTACK_KEYSTONE_URL = 'http://auth.openstack.org:5000/v3'

        projects = [self.data.project_one, self.data.project_two]
        domains = []
        unscoped = self.data.federated_unscoped_access_info
        token = unscoped.auth_token
        unscoped_auth = self._mock_plugin(unscoped)

        form_data = {'token': token}
        self._mock_federated_client_list_domains(unscoped_auth, domains)
        self._mock_federated_client_list_projects(unscoped_auth, projects)
        self._mock_scoped_client_for_tenant(unscoped, self.data.project_one.id)

        self.mox.ReplayAll()

        url = reverse('websso')

        # POST to the page to log in.
        response = self.client.post(url, form_data)
        self.assertRedirects(response, settings.LOGIN_REDIRECT_URL)

    def test_websso_login_default_redirect(self):
        origin = 'http://testserver/auth/websso/'
        protocol = 'oidc'
        redirect_url = ('%s/auth/OS-FEDERATION/websso/%s?origin=%s' %
                        (settings.OPENSTACK_KEYSTONE_URL, protocol, origin))

        settings.WEBSSO_DEFAULT_REDIRECT = True
        settings.WEBSSO_DEFAULT_REDIRECT_PROTOCOL = 'oidc'
        settings.WEBSSO_DEFAULT_REDIRECT_REGION = (
            settings.OPENSTACK_KEYSTONE_URL)

        url = reverse('login')

        # POST to the page and redirect to keystone.
        response = self.client.get(url)
        self.assertRedirects(response, redirect_url, status_code=302,
                             target_status_code=404)

    def test_websso_logout_default_redirect(self):
        settings.WEBSSO_DEFAULT_REDIRECT = True
        settings.WEBSSO_DEFAULT_REDIRECT_LOGOUT = 'http://idptest/logout'

        url = reverse('logout')

        # POST to the page and redirect to logout method from idp.
        response = self.client.get(url)
        self.assertRedirects(response, settings.WEBSSO_DEFAULT_REDIRECT_LOGOUT,
                             status_code=302, target_status_code=301)


load_tests = load_tests_apply_scenarios
