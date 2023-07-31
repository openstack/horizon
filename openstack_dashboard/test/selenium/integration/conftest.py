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

import openstack as openstack_sdk
import pytest


def create_conn(username, password, project, domain, auth_url):
    if not domain:
        domain = 'default'
    conn = openstack_sdk.connection.Connection(
        auth={
            "auth_url": auth_url,
            "user_domain_id": domain,
            "project_domain_id": domain,
            "project_name": project,
            "username": username,
            "password": password,
        },
        compute_api_version='2',
        verify=False,
    )
    conn.authorize()
    return conn


@pytest.fixture(scope='session')
def openstack_admin(config):
    conn = create_conn(
        config.identity.admin_username,
        config.identity.admin_password,
        config.identity.admin_home_project,
        config.identity.domain,
        config.dashboard.auth_url,
    )
    yield conn
    conn.close()


@pytest.fixture(scope='session')
def openstack_demo(config):
    conn = create_conn(
        config.identity.username,
        config.identity.password,
        config.identity.home_project,
        config.identity.domain,
        config.dashboard.auth_url,
    )
    yield conn
    conn.close()
