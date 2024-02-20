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

from unittest import mock
import warnings

from django.test import testcases
import pytest
import requests

from keystoneauth1.identity import v3 as v3_auth
from keystoneclient.v3 import client as client_v3
import openstack_auth
from openstack_auth.tests import data_v3
from openstack_auth import utils as auth_utils
from openstack_dashboard import api
from openstack_dashboard.test.test_data import utils as test_utils


@pytest.fixture(autouse=True, scope='session')
def no_warnings():
    warnings.simplefilter("ignore")
    yield
    warnings.simplefilter("default")


@pytest.fixture(autouse=True)
def settings_debug(settings):
    settings.DEBUG = True


@pytest.fixture(scope='session')
def auth_data():
    return data_v3.generate_test_data()


@pytest.fixture(scope='session')
def dashboard_data():
    return test_utils.load_test_data()


@pytest.fixture(autouse=True)
def disable_requests(monkeypatch):
    class MockRequestsSession:
        adapters = []

        def request(self, *args, **kwargs):
            raise RuntimeError("External request attempted, missed a mock?")

    monkeypatch.setattr(requests, 'Session', MockRequestsSession)
    # enable request logging
    monkeypatch.setattr(testcases, 'QuietWSGIRequestHandler',
                        testcases.WSGIRequestHandler)


# prevent pytest-django errors due to no database
@pytest.fixture()
def _django_db_helper():
    pass


@pytest.fixture()
def mock_openstack_auth(settings, auth_data):
    with mock.patch.object(client_v3, 'Client') as mock_client, \
            mock.patch.object(v3_auth, 'Token') as mock_token, \
            mock.patch.object(v3_auth, 'Password') as mock_password:

        keystone_url = settings.OPENSTACK_KEYSTONE_URL
        auth_password = mock.Mock(auth_url=keystone_url)
        mock_password.return_value = auth_password
        auth_password.get_access.return_value = auth_data.unscoped_access_info
        auth_token_unscoped = mock.Mock(auth_url=keystone_url)
        auth_token_scoped = mock.Mock(auth_url=keystone_url)
        mock_token.return_value = auth_token_scoped
        auth_token_unscoped.get_access.return_value = (
            auth_data.federated_unscoped_access_info
        )
        auth_token_scoped.get_access.return_value = (
            auth_data.unscoped_access_info
        )
        client_unscoped = mock.Mock()
        mock_client.return_value = client_unscoped
        projects = [auth_data.project_one, auth_data.project_two]
        client_unscoped.projects.list.return_value = projects
        yield


@pytest.fixture()
def mock_keystoneclient():
    with mock.patch.object(api.keystone, 'keystoneclient') as mock_client:
        keystoneclient = mock_client.return_value
        endpoint_data = mock.Mock()
        endpoint_data.api_version = (3, 10)
        keystoneclient.session.get_endpoint_data.return_value = endpoint_data
        yield


@pytest.fixture()
def user(monkeypatch, dashboard_data, mock_keystoneclient):
    def get_user(request):
        new_user = openstack_auth.user.User(
            id=dashboard_data.user.id,
            token=dashboard_data.token,
            user=dashboard_data.user.name,
            domain_id=dashboard_data.domain.id,
            tenant_id=dashboard_data.tenant.id,
            service_catalog=dashboard_data.service_catalog,
            authorized_tenants=dashboard_data.tenants.list(),
        )
        new_user._is_system_user = False
        return new_user
    monkeypatch.setattr(auth_utils, 'get_user', get_user)
