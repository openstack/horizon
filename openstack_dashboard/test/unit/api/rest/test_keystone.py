# Copyright 2014, Rackspace, US, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from django.conf import settings
import mock
from oslo_serialization import jsonutils

from openstack_dashboard import api
from openstack_dashboard.api.rest import keystone
from openstack_dashboard.test import helpers as test


class KeystoneRestTestCase(test.TestCase):

    #
    # Version
    #
    @test.create_mocks({api.keystone: ['get_version']})
    def test_version_get(self):
        request = self.mock_rest_request()
        self.mock_get_version.return_value = '3'
        response = keystone.Version().get(request)
        self.assertStatusCode(response, 200)
        self.assertEqual(response.json, {"version": "3"})
        self.mock_get_version.assert_called_once_with()

    #
    # Users
    #
    @test.create_mocks({api.keystone: ['user_get']})
    def test_user_get(self):
        request = self.mock_rest_request()
        self.mock_user_get.return_value.to_dict.return_value = {'name': 'Ni!'}
        response = keystone.User().get(request, 'the_id')
        self.assertStatusCode(response, 200)
        self.assertEqual(response.json, {"name": "Ni!"})
        self.mock_user_get.assert_called_once_with(
            request, 'the_id', admin=False)

    @test.create_mocks({api.keystone: ['user_get']})
    def test_user_get_current(self):
        request = self.mock_rest_request(**{'user.id': 'current_id'})
        self.mock_user_get.return_value.to_dict.return_value = {'name': 'Ni!'}
        response = keystone.User().get(request, 'current')
        self.assertStatusCode(response, 200)
        self.assertEqual(response.json, {"name": "Ni!"})
        self.mock_user_get.assert_called_once_with(
            request, 'current_id', admin=False)

    @test.create_mocks({api.keystone: ['user_list']})
    def test_user_get_list(self):
        request = self.mock_rest_request(**{
            'session.get': mock.Mock(return_value='the_domain'),
            'GET': {},
        })
        self.mock_user_list.return_value = [
            mock.Mock(**{'to_dict.return_value': {'name': 'Ni!'}}),
            mock.Mock(**{'to_dict.return_value': {'name': 'Ptang!'}})
        ]
        response = keystone.Users().get(request)
        self.assertStatusCode(response, 200)
        self.assertEqual(response.json,
                         {"items": [{"name": "Ni!"}, {"name": "Ptang!"}]})
        self.mock_user_list.assert_called_once_with(request, project=None,
                                                    domain='the_domain',
                                                    group=None,
                                                    filters=None)

    @test.create_mocks({api.keystone: ['user_list']})
    def test_user_get_list_with_filters(self):
        filters = {'enabled': True}
        request = self.mock_rest_request(**{
            'session.get': mock.Mock(return_value='the_domain'),
            'GET': dict(**filters),
        })
        self.mock_user_list.return_value = [
            mock.Mock(**{'to_dict.return_value': {'name': 'Ni!'}}),
            mock.Mock(**{'to_dict.return_value': {'name': 'Ptang!'}})
        ]
        response = keystone.Users().get(request)
        self.assertStatusCode(response, 200)
        self.assertEqual(response.json,
                         {"items": [{"name": "Ni!"}, {"name": "Ptang!"}]})
        self.mock_user_list.assert_called_once_with(request, project=None,
                                                    domain='the_domain',
                                                    group=None,
                                                    filters=filters)

    def test_user_create_full(self):
        self._test_user_create(
            '{"name": "bob", '
            '"password": "sekrit", "project": "123", '
            '"email": "spam@company.example", '
            '"description": "hello, puff"}',
            {
                'name': 'bob',
                'password': 'sekrit',
                'email': 'spam@company.example',
                'project': '123',
                'domain': 'the_domain',
                'enabled': True,
                'description': 'hello, puff'
            }
        )

    def test_user_create_existing_role(self):
        self._test_user_create(
            '{"name": "bob", '
            '"password": "sekrit", "project": "123", '
            '"email": "spam@company.example"}',
            {
                'name': 'bob',
                'password': 'sekrit',
                'email': 'spam@company.example',
                'project': '123',
                'domain': 'the_domain',
                'enabled': True,
                'description': None
            }
        )

    def test_user_create_no_project(self):
        self._test_user_create(
            '{"name": "bob", '
            '"password": "sekrit", "project": "", '
            '"email": "spam@company.example"}',
            {
                'name': 'bob',
                'password': 'sekrit',
                'email': 'spam@company.example',
                'project': None,
                'domain': 'the_domain',
                'enabled': True,
                'description': None
            }
        )

    def test_user_create_partial(self):
        self._test_user_create(
            '{"name": "bob", "project": ""}',
            {
                'name': 'bob',
                'password': None,
                'email': None,
                'project': None,
                'domain': 'the_domain',
                'enabled': True,
                'description': None
            }
        )

    @test.create_mocks({api.keystone: ['get_default_domain',
                                       'user_create']})
    def _test_user_create(self, supplied_body, add_user_call):
        request = self.mock_rest_request(body=supplied_body)
        self.mock_get_default_domain.return_value = \
            mock.Mock(**{'id': 'the_domain'})
        self.mock_user_create.return_value = mock.Mock(**{
            'id': 'user123',
            'to_dict.return_value': {'id': 'user123', 'name': 'bob'}
        })

        response = keystone.Users().post(request)
        self.assertStatusCode(response, 201)
        self.assertEqual(response['location'],
                         '/api/keystone/users/user123')
        self.assertEqual(response.json,
                         {"id": "user123", "name": "bob"})
        self.mock_user_create.assert_called_once_with(request, **add_user_call)
        self.mock_get_default_domain.assert_called_once_with(request)

    @test.create_mocks({api.keystone: ['user_delete']})
    def test_user_delete_many(self):
        request = self.mock_rest_request(body='''
            ["id1", "id2", "id3"]
        ''')
        self.mock_user_delete.return_value = None

        response = keystone.Users().delete(request)
        self.assertStatusCode(response, 204)
        self.assertEqual(response.content, b'')
        self.mock_user_delete.assert_has_calls([
            mock.call(request, 'id1'),
            mock.call(request, 'id2'),
            mock.call(request, 'id3'),
        ])

    @test.create_mocks({api.keystone: ['user_delete']})
    def test_user_delete(self):
        request = self.mock_rest_request()
        self.mock_user_delete.return_value = None
        response = keystone.User().delete(request, 'the_id')
        self.assertStatusCode(response, 204)
        self.assertEqual(response.content, b'')
        self.mock_user_delete.assert_called_once_with(request, 'the_id')

    @test.create_mocks({api.keystone: ['user_get',
                                       'user_update_password']})
    def test_user_patch_password(self):
        request = self.mock_rest_request(body='''
            {"password": "sekrit"}
        ''')
        user = keystone.User()
        self.mock_user_get.return_value = mock.sentinel.user
        self.mock_user_update_password.return_value = None
        response = user.patch(request, 'user123')
        self.assertStatusCode(response, 204)
        self.assertEqual(response.content, b'')
        self.mock_user_get.assert_called_once_with(request, 'user123')
        self.mock_user_update_password.assert_called_once_with(
            request, mock.sentinel.user, 'sekrit')

    @test.create_mocks({api.keystone: ['user_get',
                                       'user_update_enabled']})
    def test_user_patch_enabled(self):
        request = self.mock_rest_request(body='''
            {"enabled": false}
        ''')
        user = keystone.User()
        self.mock_user_get.return_value = mock.sentinel.user
        self.mock_user_update_enabled.return_value = None
        response = user.patch(request, 'user123')
        self.assertStatusCode(response, 204)
        self.assertEqual(response.content, b'')
        self.mock_user_get.assert_called_once_with(request, 'user123')
        self.mock_user_update_enabled.assert_called_once_with(
            request, mock.sentinel.user, False)

    @test.create_mocks({api.keystone: ['user_get',
                                       'user_update']})
    def test_user_patch_project(self):
        request = self.mock_rest_request(body='''
            {"project": "other123"}
        ''')
        user = keystone.User()
        self.mock_user_get.return_value = mock.sentinel.user
        self.mock_user_update.return_value = self.users.first()
        response = user.patch(request, 'user123')
        self.assertStatusCode(response, 204)
        self.assertEqual(response.content, b'')
        self.mock_user_get.assert_called_once_with(request, 'user123')
        self.mock_user_update.assert_called_once_with(
            request, mock.sentinel.user, project='other123')

    @test.create_mocks({api.keystone: ['user_get',
                                       'user_update']})
    def test_user_patch_multiple(self):
        request = self.mock_rest_request(body='''
            {"project": "other123", "name": "something"}
        ''')
        user = keystone.User()
        self.mock_user_get.return_value = mock.sentinel.user
        self.mock_user_update.return_value = self.users.first()
        response = user.patch(request, 'user123')
        self.assertStatusCode(response, 204)
        self.assertEqual(response.content, b'')
        self.mock_user_get.assert_called_once_with(request, 'user123')
        self.mock_user_update.assert_called_once_with(
            request, mock.sentinel.user, project='other123', name='something')

    #
    # Roles
    #
    @test.create_mocks({api.keystone: ['role_get']})
    def test_role_get(self):
        request = self.mock_rest_request()
        self.mock_role_get.return_value.to_dict.return_value = {'name': 'Ni!'}
        response = keystone.Role().get(request, 'the_id')
        self.assertStatusCode(response, 200)
        self.assertEqual(response.json, {"name": "Ni!"})
        self.mock_role_get.assert_called_once_with(request, 'the_id')

    @test.create_mocks({api.keystone: ['get_default_role']})
    def test_role_get_default(self):
        request = self.mock_rest_request()
        ret_val_role = self.mock_get_default_role.return_value
        ret_val_role.to_dict.return_value = {'name': 'Ni!'}
        response = keystone.Role().get(request, 'default')
        self.assertStatusCode(response, 200)
        self.assertEqual(response.json, {"name": "Ni!"})
        self.mock_get_default_role.assert_called_once_with(request)

    @test.create_mocks({api.keystone: ['role_list']})
    def test_role_get_list(self):
        request = self.mock_rest_request(**{'GET': {}})
        self.mock_role_list.return_value = [
            mock.Mock(**{'to_dict.return_value': {'name': 'Ni!'}}),
            mock.Mock(**{'to_dict.return_value': {'name': 'Ptang!'}})
        ]
        response = keystone.Roles().get(request)
        self.assertStatusCode(response, 200)
        self.assertEqual(response.json,
                         {"items": [{"name": "Ni!"}, {"name": "Ptang!"}]})
        self.mock_role_list.assert_called_once_with(request)

    @test.create_mocks({api.keystone: ['roles_for_user']})
    def test_role_get_for_user(self):
        request = self.mock_rest_request(**{'GET': {'user_id': 'user123',
                                         'project_id': 'project123'}})
        self.mock_roles_for_user.return_value = [
            mock.Mock(**{'to_dict.return_value': {'name': 'Ni!'}}),
            mock.Mock(**{'to_dict.return_value': {'name': 'Ptang!'}})
        ]
        response = keystone.Roles().get(request)
        self.assertStatusCode(response, 200)
        self.assertEqual(response.json,
                         {"items": [{"name": "Ni!"}, {"name": "Ptang!"}]})
        self.mock_roles_for_user.assert_called_once_with(request, 'user123',
                                                         'project123')

    @test.create_mocks({api.keystone: ['role_create']})
    def test_role_create(self):
        request = self.mock_rest_request(body='''
            {"name": "bob"}
        ''')
        self.mock_role_create.return_value.id = 'role123'
        self.mock_role_create.return_value.to_dict.return_value = {
            'id': 'role123', 'name': 'bob'
        }

        response = keystone.Roles().post(request)
        self.assertStatusCode(response, 201)
        self.assertEqual(response['location'],
                         '/api/keystone/roles/role123')
        self.assertEqual(response.json, {"id": "role123", "name": "bob"})
        self.mock_role_create.assert_called_once_with(request, 'bob')

    @test.create_mocks({api.keystone: ['add_tenant_user_role']})
    def test_role_grant(self):
        self.mock_add_tenant_user_role.return_value = None
        request = self.mock_rest_request(body='''
            {"action": "grant", "data": {"user_id": "user123",
            "role_id": "role123", "project_id": "project123"}}
        ''')
        response = keystone.ProjectRole().put(request, "project1", "role2",
                                              "user3")
        self.assertStatusCode(response, 204)
        self.assertEqual(response.content, b'')
        self.mock_add_tenant_user_role.assert_called_once_with(
            request, 'project1', 'user3', 'role2')

    @test.create_mocks({api.keystone: ['role_delete']})
    def test_role_delete_many(self):
        self.mock_role_delete.return_value = None
        request = self.mock_rest_request(body='''
            ["id1", "id2", "id3"]
        ''')

        response = keystone.Roles().delete(request)
        self.assertStatusCode(response, 204)
        self.assertEqual(response.content, b'')
        self.mock_role_delete.assert_has_calls([
            mock.call(request, 'id1'),
            mock.call(request, 'id2'),
            mock.call(request, 'id3'),
        ])

    @test.create_mocks({api.keystone: ['role_delete']})
    def test_role_delete(self):
        self.mock_role_delete.return_value = None
        request = self.mock_rest_request()
        response = keystone.Role().delete(request, 'the_id')
        self.assertStatusCode(response, 204)
        self.assertEqual(response.content, b'')
        self.mock_role_delete.assert_called_once_with(request, 'the_id')

    @test.create_mocks({api.keystone: ['role_update']})
    def test_role_patch(self):
        self.mock_role_update.return_value = self.roles.first()
        request = self.mock_rest_request(body='{"name": "spam"}')
        response = keystone.Role().patch(request, 'the_id')
        self.assertStatusCode(response, 204)
        self.assertEqual(response.content, b'')
        self.mock_role_update.assert_called_once_with(request,
                                                      'the_id',
                                                      'spam')

    #
    # Domains
    #
    @test.create_mocks({api.keystone: ['get_default_domain']})
    def test_default_domain_get(self):
        request = self.mock_rest_request()
        domain = api.base.APIDictWrapper({'id': 'the_id', 'name': 'the_name'})
        self.mock_get_default_domain.return_value = domain
        response = keystone.DefaultDomain().get(request)
        self.assertStatusCode(response, 200)
        self.assertEqual(response.json, domain.to_dict())
        self.mock_get_default_domain.assert_called_once_with(request)

    @test.create_mocks({api.keystone: ['domain_get']})
    def test_domain_get(self):
        request = self.mock_rest_request()
        ret_val_domain = self.mock_domain_get.return_value
        ret_val_domain.to_dict.return_value = {'name': 'Ni!'}
        response = keystone.Domain().get(request, 'the_id')
        self.assertStatusCode(response, 200)
        self.assertEqual(response.json, {"name": "Ni!"})
        self.mock_domain_get.assert_called_once_with(request, 'the_id')

    @test.create_mocks({api.keystone: ['get_default_domain']})
    def test_domain_get_default(self):
        request = self.mock_rest_request()
        self.mock_get_default_domain.return_value.to_dict.return_value = {
            'name': 'Ni!'
        }
        response = keystone.Domain().get(request, 'default')
        self.assertStatusCode(response, 200)
        self.assertEqual(response.json, {"name": "Ni!"})
        self.mock_get_default_domain.assert_called_once_with(request)

    @test.create_mocks({api.keystone: ['domain_list']})
    def test_domain_get_list(self):
        request = self.mock_rest_request()
        self.mock_domain_list.return_value = [
            mock.Mock(**{'to_dict.return_value': {'name': 'Ni!'}}),
            mock.Mock(**{'to_dict.return_value': {'name': 'Ptang!'}})
        ]
        response = keystone.Domains().get(request)
        self.assertStatusCode(response, 200)
        self.assertEqual(response.json,
                         {"items": [{"name": "Ni!"}, {"name": "Ptang!"}]})
        self.mock_domain_list.assert_called_once_with(request)

    def test_domain_create_full(self):
        self._test_domain_create(
            '{"name": "bob", '
            '"description": "sekrit", "enabled": false}',
            {
                'description': 'sekrit',
                'enabled': False
            }
        )

    def test_domain_create_partial(self):
        self._test_domain_create(
            '{"name": "bob"}',
            {
                'description': None,
                'enabled': True
            }
        )

    @test.create_mocks({api.keystone: ['domain_create']})
    def _test_domain_create(self, supplied_body, expected_call):
        request = self.mock_rest_request(body=supplied_body)
        ret_val_domain = self.mock_domain_create.return_value
        ret_val_domain.id = 'domain123'
        ret_val_domain.to_dict.return_value = {
            'id': 'domain123', 'name': 'bob'
        }

        response = keystone.Domains().post(request)
        self.assertStatusCode(response, 201)
        self.assertEqual(response['location'],
                         '/api/keystone/domains/domain123')
        self.assertEqual(response.json, {"id": "domain123", "name": "bob"})
        self.mock_domain_create.assert_called_once_with(request, 'bob',
                                                        **expected_call)

    @test.create_mocks({api.keystone: ['domain_delete']})
    def test_domain_delete_many(self):
        self.mock_domain_delete.return_value = None
        request = self.mock_rest_request(body='''
            ["id1", "id2", "id3"]
        ''')

        response = keystone.Domains().delete(request)
        self.assertStatusCode(response, 204)
        self.assertEqual(response.content, b'')
        self.mock_domain_delete.assert_has_calls([
            mock.call(request, 'id1'),
            mock.call(request, 'id2'),
            mock.call(request, 'id3'),
        ])

    @test.create_mocks({api.keystone: ['domain_delete']})
    def test_domain_delete(self):
        self.mock_domain_delete.return_value = None
        request = self.mock_rest_request()
        response = keystone.Domain().delete(request, 'the_id')
        self.assertStatusCode(response, 204)
        self.assertEqual(response.content, b'')
        self.mock_domain_delete.assert_called_once_with(request, 'the_id')

    @test.create_mocks({api.keystone: ['domain_update']})
    def test_domain_patch(self):
        self.mock_domain_update.return_value = self.domains.first()
        request = self.mock_rest_request(body='{"name": "spam"}')
        response = keystone.Domain().patch(request, 'the_id')
        self.assertStatusCode(response, 204)
        self.assertEqual(response.content, b'')
        self.mock_domain_update.assert_called_once_with(request,
                                                        'the_id',
                                                        name='spam',
                                                        description=None,
                                                        enabled=None)

    #
    # Projects
    #
    @test.create_mocks({api.keystone: ['tenant_get']})
    def test_project_get(self):
        request = self.mock_rest_request()
        ret_val_tenant = self.mock_tenant_get.return_value
        ret_val_tenant.to_dict.return_value = {'name': 'Ni!'}
        response = keystone.Project().get(request, 'the_id')
        self.assertStatusCode(response, 200)
        self.assertEqual(response.json, {"name": "Ni!"})
        self.mock_tenant_get.assert_called_once_with(
            request, 'the_id', admin=False)

    def test_project_get_list(self):
        self._test_project_get_list(
            {},
            {
                'paginate': False,
                'marker': None,
                'domain': None,
                'user': None,
                'admin': True,
                'filters': None
            }
        )

    def test_project_get_list_with_params_true(self):
        self._test_project_get_list(
            {
                'paginate': 'true',
                'admin': 'true'
            },
            {
                'paginate': True,
                'marker': None,
                'domain': None,
                'user': None,
                'admin': True,
                'filters': None
            }
        )

    def test_project_get_list_with_params_false(self):
        self._test_project_get_list(
            {
                'paginate': 'false',
                'admin': 'false'
            },
            {
                'paginate': False,
                'marker': None,
                'domain': None,
                'user': None,
                'admin': False,
                'filters': None
            }
        )

    @test.create_mocks({api.keystone: ['tenant_list']})
    def _test_project_get_list(self, params, expected_call):
        request = self.mock_rest_request(**{'GET': dict(**params)})
        self.mock_tenant_list.return_value = ([
            mock.Mock(**{'to_dict.return_value': {'name': 'Ni!'}}),
            mock.Mock(**{'to_dict.return_value': {'name': 'Ptang!'}})
        ], False)
        with mock.patch.object(settings, 'DEBUG', True):
            response = keystone.Projects().get(request)
        self.assertStatusCode(response, 200)
        self.assertEqual(response.json,
                         {"has_more": False,
                          "items": [{"name": "Ni!"}, {"name": "Ptang!"}]})
        self.mock_tenant_list.assert_called_once_with(request, **expected_call)

    @test.create_mocks({api.keystone: ['tenant_list']})
    def test_project_get_list_with_filters(self):
        filters = {'name': 'Ni!'}
        request = self.mock_rest_request(**{'GET': dict(**filters)})
        self.mock_tenant_list.return_value = ([
            mock.Mock(**{'to_dict.return_value': {'name': 'Ni!'}}),
            mock.Mock(**{'to_dict.return_value': {'name': 'Ni!'}})
        ], False)
        with mock.patch.object(settings, 'DEBUG', True):
            response = keystone.Projects().get(request)
        self.assertStatusCode(response, 200)
        self.assertEqual(response.json,
                         {"has_more": False,
                          "items": [{"name": "Ni!"}, {"name": "Ni!"}]})
        self.mock_tenant_list.assert_called_once_with(request, paginate=False,
                                                      marker=None, domain=None,
                                                      user=None, admin=True,
                                                      filters=filters)

    def test_project_create_full(self):
        self._test_project_create(
            '{"name": "bob", '
            '"domain_id": "domain123", "description": "sekrit", '
            '"enabled": false}',
            {
                'name': 'bob',
                'description': 'sekrit',
                'domain': 'domain123',
                'enabled': False
            }
        )

    def test_project_create_partial(self):
        self._test_project_create(
            '{"name": "bob"}',
            {
                'name': 'bob',
                'description': None,
                'domain': None,
                'enabled': True
            }
        )

    @test.create_mocks({api.keystone: ['tenant_create']})
    def _test_project_create(self, supplied_body, expected_args):
        request = self.mock_rest_request(body=supplied_body)
        self.mock_tenant_create.return_value.id = 'project123'
        self.mock_tenant_create.return_value.to_dict.return_value = {
            'id': 'project123', 'name': 'bob'
        }

        response = keystone.Projects().post(request)
        self.assertStatusCode(response, 201)
        self.assertEqual(response['location'],
                         '/api/keystone/projects/project123')
        self.assertEqual(response.json,
                         {"id": "project123", "name": "bob"})
        self.mock_tenant_create.assert_called_once_with(request,
                                                        **expected_args)

    @test.create_mocks({api.keystone: ['tenant_delete']})
    def test_project_delete_many(self):
        self.mock_tenant_delete.return_value = None
        request = self.mock_rest_request(body='''
            ["id1", "id2", "id3"]
        ''')

        response = keystone.Projects().delete(request)
        self.assertStatusCode(response, 204)
        self.assertEqual(response.content, b'')
        self.mock_tenant_delete.assert_has_calls([
            mock.call(request, 'id1'),
            mock.call(request, 'id2'),
            mock.call(request, 'id3'),
        ])

    @test.create_mocks({api.keystone: ['tenant_delete']})
    def test_project_delete(self):
        self.mock_tenant_delete.return_value = None
        request = self.mock_rest_request()
        response = keystone.Project().delete(request, 'the_id')
        self.assertStatusCode(response, 204)
        self.assertEqual(response.content, b'')
        self.mock_tenant_delete.assert_called_once_with(request, 'the_id')

    @test.create_mocks({api.keystone: ['tenant_update']})
    def test_project_patch(self):
        # nothing in the Horizon code documents what additional parameters are
        # allowed, so we'll just assume GIGO
        self.mock_tenant_update.return_value = self.tenants.first()
        request = self.mock_rest_request(body='''
            {"name": "spam", "domain_id": "domain123", "foo": "bar"}
        ''')
        response = keystone.Project().patch(request, 'spam123')
        self.assertStatusCode(response, 204)
        self.assertEqual(response.content, b'')
        self.mock_tenant_update.assert_called_once_with(request,
                                                        'spam123',
                                                        name='spam', foo='bar',
                                                        description=None,
                                                        domain='domain123',
                                                        enabled=None)

    #
    # Service Catalog
    #
    def test_service_catalog_get(self):
        request = self.mock_rest_request()
        request.user = mock.MagicMock(**{'service_catalog': [
            {'endpoints': [
                {'url': 'http://cool_url/image',
                 'interface': 'admin',
                 'region': 'RegionOne',
                 'region_id': 'RegionOne',
                 'id': 'test'},
                {'url': 'http://cool_url/image',
                 'interface': 'public',
                 'region': 'RegionOne',
                 'region_id': 'RegionOne',
                 'id': 'test'},
                {'url': 'http://cool_url/image',
                 'interface': 'internal',
                 'region': 'RegionOne',
                 'region_id': 'RegionOne',
                 'id': 'test'}],
                'type': 'image',
                'id': '2b5bc2e59b094f898a43f5e8ce446240',
                'name': 'glance'},
            {'endpoints': [
                {'url': 'http://cool_url/volume/v2/test',
                 'interface': 'public',
                 'region': 'RegionOne',
                 'region_id': 'RegionOne',
                 'id': '29a629afb80547ea9baa4266e97b4cb5'},
                {'url': 'http://cool_url/volume/v2/test',
                 'interface': 'admin',
                 'region': 'RegionOne',
                 'region_id': 'RegionOne',
                 'id': '29a629afb80547ea9baa4266e97b4cb5'}],
                'type': 'volumev2',
                'id': '55ef272cfa714e54b8f2046c157b027d',
                'name': 'cinderv2'},
            {'endpoints': [
                {'url': 'http://cool_url/compute/v2/check',
                 'interface': 'internal',
                 'region': 'RegionOne',
                 'region_id': 'RegionOne',
                 'id': 'e8c440e025d94355ab82c78cc2062129'}],
                'type': 'compute_legacy',
                'id': 'b7f1d3f4119643508d5ca2325eb8af87',
                'name': 'nova_legacy'}]})
        response = keystone.ServiceCatalog().get(request)
        self.assertStatusCode(response, 200)
        content = [{'endpoints': [
                    {'url': 'http://cool_url/image',
                     'interface': 'public',
                     'region': 'RegionOne',
                     'region_id': 'RegionOne',
                     'id': 'test'}],
                    'type': 'image',
                    'id': '2b5bc2e59b094f898a43f5e8ce446240',
                    'name': 'glance'},
                   {'endpoints': [
                    {'url': 'http://cool_url/volume/v2/test',
                     'interface': 'public',
                     'region': 'RegionOne',
                     'region_id': 'RegionOne',
                     'id': '29a629afb80547ea9baa4266e97b4cb5'}],
                    'type': 'volumev2',
                    'id': '55ef272cfa714e54b8f2046c157b027d',
                    'name': 'cinderv2'}]
        self.assertEqual(content, jsonutils.loads(response.content))

    #
    # User Session
    #
    def test_user_session_get(self):
        request = self.mock_rest_request()
        request.user = mock.Mock(
            services_region='some region',
            super_secret_thing='not here',
            token=type('', (object,), {'id': 'token here'}),
            is_authenticated=lambda: True,
            spec=['services_region', 'super_secret_thing']
        )
        response = keystone.UserSession().get(request)
        self.assertStatusCode(response, 200)
        content = jsonutils.loads(response.content)
        self.assertEqual(content['services_region'], 'some region')
        self.assertEqual(content['token'], 'token here')
        self.assertNotIn('super_secret_thing', content)

    #
    # Groups
    #
    @test.create_mocks({api.keystone: ['group_list']})
    def test_group_get_list(self):
        request = self.mock_rest_request(**{
            'session.get': mock.Mock(return_value='the_domain'),
            'GET': {},
        })
        self.mock_group_list.return_value = [
            mock.Mock(**{'to_dict.return_value': {'name': 'uno!'}}),
            mock.Mock(**{'to_dict.return_value': {'name': 'dos!'}})
        ]
        response = keystone.Groups().get(request)
        self.assertStatusCode(response, 200)
        self.assertEqual(response.json,
                         {"items": [{"name": "uno!"}, {"name": "dos!"}]})
        self.mock_group_list.assert_called_once_with(request,
                                                     domain='the_domain')

    @test.create_mocks({api.keystone: ['group_create']})
    def test_group_create(self):
        request = self.mock_rest_request(**{
            'session.get': mock.Mock(return_value='the_domain'),
            'GET': {},
            'body': '{"name": "bug!", "description": "bugaboo!!"}',
        })
        self.mock_group_create.return_value.id = 'group789'
        self.mock_group_create.return_value.to_dict.return_value = {
            'id': 'group789', 'name': 'bug!', 'description': 'bugaboo!!'
        }

        response = keystone.Groups().post(request)
        self.assertStatusCode(response, 201)
        self.assertEqual(response['location'],
                         '/api/keystone/groups/group789')
        self.assertEqual(response.json,
                         {"id": "group789",
                          "name": "bug!",
                          "description": "bugaboo!!"})
        self.mock_group_create.assert_called_once_with(request, 'the_domain',
                                                       'bug!', 'bugaboo!!')

    @test.create_mocks({api.keystone: ['group_create']})
    def test_group_create_without_description(self):
        request = self.mock_rest_request(**{
            'session.get': mock.Mock(return_value='the_domain'),
            'GET': {},
            'body': '{"name": "bug!"}',
        })
        self.mock_group_create.return_value.id = 'group789'
        self.mock_group_create.return_value.to_dict.return_value = {
            'id': 'group789', 'name': 'bug!'
        }

        response = keystone.Groups().post(request)
        self.assertStatusCode(response, 201)
        self.assertEqual(response['location'],
                         '/api/keystone/groups/group789')
        self.assertEqual(response.json,
                         {"id": "group789",
                          "name": "bug!"})
        self.mock_group_create.assert_called_once_with(request, 'the_domain',
                                                       'bug!', None)

    @test.create_mocks({api.keystone: ['group_get']})
    def test_group_get(self):
        request = self.mock_rest_request()
        self.mock_group_get.return_value.to_dict.return_value = {
            'name': 'bug!', 'description': 'bugaboo!!'}
        response = keystone.Group().get(request, 'the_id')
        self.assertStatusCode(response, 200)
        self.assertEqual(response.json, {"name": "bug!",
                         "description": "bugaboo!!"})
        self.mock_group_get.assert_called_once_with(request, 'the_id')

    @test.create_mocks({api.keystone: ['group_delete']})
    def test_group_delete(self):
        self.mock_group_delete.return_value = None
        request = self.mock_rest_request()
        response = keystone.Group().delete(request, 'the_id')
        self.assertStatusCode(response, 204)
        self.assertEqual(response.content, b'')
        self.mock_group_delete.assert_called_once_with(request, 'the_id')

    @test.create_mocks({api.keystone: ['group_update']})
    def test_group_patch(self):
        self.mock_group_update.return_value = self.groups.first()
        request = self.mock_rest_request(
            body='{"name": "spam_i_am", "description": "Sir Spam"}')
        response = keystone.Group().patch(request, 'the_id')
        self.assertStatusCode(response, 204)
        self.assertEqual(response.content, b'')
        self.mock_group_update.assert_called_once_with(request,
                                                       'the_id',
                                                       'spam_i_am',
                                                       'Sir Spam')

    @test.create_mocks({api.keystone: ['group_delete']})
    def test_group_delete_many(self):
        self.mock_group_delete.return_value = None
        request = self.mock_rest_request(body='''
            ["id1", "id2", "id3"]
        ''')

        response = keystone.Groups().delete(request)
        self.assertStatusCode(response, 204)
        self.assertEqual(response.content, b'')
        self.mock_group_delete.assert_has_calls([
            mock.call(request, 'id1'),
            mock.call(request, 'id2'),
            mock.call(request, 'id3'),
        ])

    #
    # Services
    #

    @test.create_mocks({api.keystone: ['Service']})
    def test_services_get(self):
        request = self.mock_rest_request()
        mock_service = {
            "name": "srv_name",
            "type": "srv_type",
            "host": "srv_host"
        }
        request.user = mock.Mock(
            service_catalog=[mock_service],
            services_region='some region'
        )
        self.mock_Service.return_value.to_dict.return_value = mock_service

        response = keystone.Services().get(request)
        self.assertStatusCode(response, 200)
        self.mock_Service.assert_called_once_with(mock_service, "some region")
