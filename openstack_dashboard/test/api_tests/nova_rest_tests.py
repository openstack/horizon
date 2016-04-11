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
import mock

from django.conf import settings
from json import loads as to_json

from openstack_dashboard import api
from openstack_dashboard.api.rest import nova
from openstack_dashboard.test import helpers as test

from novaclient import exceptions


class NovaRestTestCase(test.TestCase):
    #
    # Keypairs
    #
    @mock.patch.object(nova.api, 'nova')
    def test_keypair_get(self, nc):
        request = self.mock_rest_request()
        nc.keypair_list.return_value = [
            mock.Mock(**{'to_dict.return_value': {'id': 'one'}}),
            mock.Mock(**{'to_dict.return_value': {'id': 'two'}}),
        ]
        response = nova.Keypairs().get(request)
        self.assertStatusCode(response, 200)
        self.assertEqual(response.json,
                         {"items": [{"id": "one"}, {"id": "two"}]})
        nc.keypair_list.assert_called_once_with(request)

    @mock.patch.object(nova.api, 'nova')
    def test_keypair_create(self, nc):
        request = self.mock_rest_request(body='''{"name": "Ni!"}''')
        new = nc.keypair_create.return_value
        new.to_dict.return_value = {'name': 'Ni!', 'public_key': 'sekrit'}
        new.name = 'Ni!'
        with mock.patch.object(settings, 'DEBUG', True):
            response = nova.Keypairs().post(request)
        self.assertStatusCode(response, 201)
        self.assertEqual(response.json,
                         {"name": "Ni!", "public_key": "sekrit"})
        self.assertEqual(response['location'], '/api/nova/keypairs/Ni%21')
        nc.keypair_create.assert_called_once_with(request, 'Ni!')

    @mock.patch.object(nova.api, 'nova')
    def test_keypair_import(self, nc):
        request = self.mock_rest_request(body='''
            {"name": "Ni!", "public_key": "hi"}
        ''')
        new = nc.keypair_import.return_value
        new.to_dict.return_value = {'name': 'Ni!', 'public_key': 'hi'}
        new.name = 'Ni!'
        with mock.patch.object(settings, 'DEBUG', True):
            response = nova.Keypairs().post(request)
        self.assertStatusCode(response, 201)
        self.assertEqual(response.json,
                         {"name": "Ni!", "public_key": "hi"})
        self.assertEqual(response['location'], '/api/nova/keypairs/Ni%21')
        nc.keypair_import.assert_called_once_with(request, 'Ni!', 'hi')

    def test_keypair_create_and_download(self):
        self._test_keypair_create_and_download(False)

    def test_keypair_recreate_and_download(self):
        self._test_keypair_create_and_download(True)

    @mock.patch.object(nova.api, 'nova')
    def _test_keypair_create_and_download(self, recreate_keypair, nc):
        params = {}

        if recreate_keypair:
            params = {'regenerate': 'true'}

        request = self.mock_rest_request(GET=params)

        keypair_create_response = mock.Mock()
        keypair_create_response.private_key = "private key content"
        nc.keypair_create.return_value = keypair_create_response

        with mock.patch.object(settings, 'DEBUG', True):
            response = nova.Keypair().get(request, "Ni!")

        if recreate_keypair:
            nc.keypair_delete.assert_called_once_with(request, 'Ni!')
        else:
            nc.keypair_delete.assert_not_called()

        nc.keypair_create.assert_called_once_with(request, 'Ni!')
        self.assertStatusCode(response, 200)
        self.assertEqual(
            response['Content-Disposition'],
            'attachment; filename=ni.pem')
        self.assertEqual(
            response.content.decode('utf-8'),
            "private key content")
        self.assertEqual(response['Content-Length'], '19')

    @mock.patch.object(nova.api, 'nova')
    def test_keypair_fail_to_create_because_already_exists(self, nc):
        request = self.mock_rest_request(GET={})

        conflict_exception = exceptions.Conflict(409, 'keypair exists!')
        nc.keypair_create.side_effect = conflict_exception

        with mock.patch.object(settings, 'DEBUG', True):
            response = nova.Keypair().get(request, "Ni!")

        self.assertEqual(response.status_code, 409)

    @mock.patch.object(nova.api, 'nova')
    def test_keypair_fail_to_create(self, nc):
        request = self.mock_rest_request(GET={})

        surprise_exception = exceptions.ClientException(501, 'Boom!')
        nc.keypair_create.side_effect = surprise_exception

        with mock.patch.object(settings, 'DEBUG', True):
            response = nova.Keypair().get(request, "Ni!")

        self.assertEqual(response.status_code, 500)

    #
    # Availability Zones
    #
    def test_availzone_get_brief(self):
        self._test_availzone_get(False)

    def test_availzone_get_detailed(self):
        self._test_availzone_get(True)

    @mock.patch.object(nova.api, 'nova')
    def _test_availzone_get(self, detail, nc):
        if detail:
            request = self.mock_rest_request(GET={'detailed': 'true'})
        else:
            request = self.mock_rest_request(GET={})
        nc.availability_zone_list.return_value = [
            mock.Mock(**{'to_dict.return_value': {'id': 'one'}}),
            mock.Mock(**{'to_dict.return_value': {'id': 'two'}}),
        ]
        response = nova.AvailabilityZones().get(request)
        self.assertStatusCode(response, 200)
        self.assertEqual(response.json,
                         {"items": [{"id": "one"}, {"id": "two"}]})
        nc.availability_zone_list.assert_called_once_with(request, detail)

    #
    # Limits
    #
    def test_limits_get_not_reserved(self):
        self._test_limits_get(False)

    def test_limits_get_reserved(self):
        self._test_limits_get(True)

    @mock.patch.object(nova.api, 'nova')
    def _test_limits_get(self, reserved, nc):
        if reserved:
            request = self.mock_rest_request(GET={'reserved': 'true'})
        else:
            request = self.mock_rest_request(GET={})
        nc.tenant_absolute_limits.return_value = {'id': 'one'}
        response = nova.Limits().get(request)
        self.assertStatusCode(response, 200)
        nc.tenant_absolute_limits.assert_called_once_with(request, reserved)
        self.assertEqual(response.json, {"id": "one"})

    #
    # Servers
    #
    @mock.patch.object(nova.api, 'nova')
    def test_server_create_missing(self, nc):
        request = self.mock_rest_request(body='''{"name": "hi"}''')
        response = nova.Servers().post(request)
        self.assertStatusCode(response, 400)
        self.assertEqual(response.json,
                         "missing required parameter 'source_id'")
        nc.server_create.assert_not_called()

    @mock.patch.object(nova.api, 'nova')
    def test_server_create_basic(self, nc):
        request = self.mock_rest_request(body='''{"name": "Ni!",
            "source_id": "image123", "flavor_id": "flavor123",
            "key_name": "sekrit", "user_data": "base64 yes",
            "security_groups": [{"name": "root"}]}
        ''')
        new = nc.server_create.return_value
        new.to_dict.return_value = {'id': 'server123'}
        new.id = 'server123'
        response = nova.Servers().post(request)
        self.assertStatusCode(response, 201)
        self.assertEqual(response.json, {"id": "server123"})
        self.assertEqual(response['location'], '/api/nova/servers/server123')
        nc.server_create.assert_called_once_with(
            request, 'Ni!', 'image123', 'flavor123', 'sekrit', 'base64 yes',
            [{'name': 'root'}]
        )

    @mock.patch.object(nova.api, 'nova')
    def test_server_list(self, nc):
        request = self.mock_rest_request()
        nc.server_list.return_value = ([
            mock.Mock(**{'to_dict.return_value': {'id': 'one'}}),
            mock.Mock(**{'to_dict.return_value': {'id': 'two'}}),
        ], False)

        response = nova.Servers().get(request)
        self.assertStatusCode(response, 200)
        self.assertEqual(response.json,
                         {'items': [{'id': 'one'}, {'id': 'two'}]})
        nc.server_list.assert_called_once_with(request)

    @mock.patch.object(nova.api, 'nova')
    def test_server_get_single(self, nc):
        request = self.mock_rest_request()
        nc.server_get.return_value.to_dict.return_value = {'name': '1'}

        response = nova.Server().get(request, "1")
        self.assertStatusCode(response, 200)
        nc.server_get.assert_called_once_with(request, "1")

    #
    # Server Metadata
    #
    @mock.patch.object(nova.api, 'nova')
    def test_server_get_metadata(self, nc):
        request = self.mock_rest_request()
        meta = {'foo': 'bar'}
        nc.server_get.return_value.to_dict.return_value.get.return_value = meta

        response = nova.ServerMetadata().get(request, "1")
        self.assertStatusCode(response, 200)
        nc.server_get.assert_called_once_with(request, "1")

    @mock.patch.object(nova.api, 'nova')
    def test_server_edit_metadata(self, nc):
        request = self.mock_rest_request(
            body='{"updated": {"a": "1", "b": "2"}, "removed": ["c", "d"]}'
        )

        response = nova.ServerMetadata().patch(request, '1')
        self.assertStatusCode(response, 204)
        self.assertEqual(response.content, b'')
        nc.server_metadata_update.assert_called_once_with(
            request, '1', {'a': '1', 'b': '2'}
        )
        nc.server_metadata_delete.assert_called_once_with(
            request, '1', ['c', 'd']
        )

    #
    # Extensions
    #
    @mock.patch.object(nova.api, 'nova')
    @mock.patch.object(settings,
                       'OPENSTACK_NOVA_EXTENSIONS_BLACKLIST', ['baz'])
    def _test_extension_list(self, nc):
        request = self.mock_rest_request()
        nc.list_extensions.return_value = [
            mock.Mock(**{'to_dict.return_value': {'name': 'foo'}}),
            mock.Mock(**{'to_dict.return_value': {'name': 'bar'}}),
            mock.Mock(**{'to_dict.return_value': {'name': 'baz'}}),
        ]
        response = nova.Extensions().get(request)
        self.assertStatusCode(response, 200)
        self.assertEqual(response.json,
                         {"items": [{"name": "foo"}, {"name": "bar"}]})
        nc.list_extensions.assert_called_once_with(request)

    #
    # Flavors
    #

    @mock.patch.object(nova.api, 'nova')
    def test_flavor_get_single_with_access_list(self, nc):
        request = self.mock_rest_request(GET={'get_access_list': 'tRuE'})
        nc.flavor_get.return_value.to_dict.return_value = {'name': '1'}
        nc.flavor_get.return_value.is_public = False

        nc.flavor_access_list.return_value = [
            mock.Mock(**{'tenant_id': '11'}),
            mock.Mock(**{'tenant_id': '22'}),
        ]

        response = nova.Flavor().get(request, "1")

        self.assertStatusCode(response, 200)
        self.assertEqual(to_json(response.content.decode('utf-8')),
                         to_json('{"access-list": ["11", "22"], "name": "1"}'))

        nc.flavor_get.assert_called_once_with(request, "1",
                                              get_extras=False)

    def test_get_extras_no(self):
        self._test_flavor_get_single(get_extras=False)

    def test_get_extras_yes(self):
        self._test_flavor_get_single(get_extras=True)

    def test_get_extras_default(self):
        self._test_flavor_get_single(get_extras=None)

    @mock.patch.object(nova.api, 'nova')
    def _test_flavor_get_single(self, nc, get_extras):
        if get_extras:
            request = self.mock_rest_request(GET={'get_extras': 'tRuE'})
        elif get_extras is None:
            request = self.mock_rest_request()
            get_extras = False
        else:
            request = self.mock_rest_request(GET={'get_extras': 'fAlsE'})
        nc.flavor_get.return_value.to_dict.return_value = {'name': '1'}

        response = nova.Flavor().get(request, "1")
        self.assertStatusCode(response, 200)
        if get_extras:
            self.assertEqual(response.json, {"extras": {}, "name": "1"})
        else:
            self.assertEqual(response.json, {"name": "1"})
        nc.flavor_get.assert_called_once_with(request, "1",
                                              get_extras=get_extras)

    @mock.patch.object(nova.api, 'nova')
    def test_flavor_get_single_with_swap_set_to_empty(self, nc):
        request = self.mock_rest_request()
        nc.flavor_get.return_value\
            .to_dict.return_value = {'name': '1', 'swap': ''}

        response = nova.Flavor().get(request, "1")

        self.assertStatusCode(response, 200)
        self.assertEqual(to_json(response.content.decode('utf-8')),
                         to_json('{"name": "1", "swap": 0}'))

    @mock.patch.object(nova.api, 'nova')
    def test_flavor_delete(self, nc):
        request = self.mock_rest_request()
        nova.Flavor().delete(request, "1")
        nc.flavor_delete.assert_called_once_with(request, "1")

    @mock.patch.object(nova.api, 'nova')
    def test_flavor_create(self, nc):
        flavor_req_data = '{"name": "flavor", ' \
                          '"ram": 12, ' \
                          '"vcpus": 1, ' \
                          '"disk": 2, ' \
                          '"OS-FLV-EXT-DATA:ephemeral": 3, ' \
                          '"swap": 4, ' \
                          '"id": "123"' \
                          '}'

        nc.flavor_create.return_value = mock.Mock(**{
            'id': '123',
            'to_dict.return_value': {'id': '123', 'name': 'flavor'}
        })

        flavor_data = {'name': 'flavor',
                       'memory': 12,
                       'vcpu': 1,
                       'disk': 2,
                       'ephemeral': 3,
                       'swap': 4,
                       'flavorid': '123',
                       'is_public': True}

        request = self.mock_rest_request(body=flavor_req_data)
        response = nova.Flavors().post(request)

        self.assertStatusCode(response, 201)
        self.assertEqual(response['location'], '/api/nova/flavors/123')

        nc.flavor_create.assert_called_once_with(request, **flavor_data)

    @mock.patch.object(nova.api, 'nova')
    def test_flavor_create_with_access_list(self, nc):
        flavor_req_data = '{"name": "flavor", ' \
                          '"ram": 12, ' \
                          '"vcpus": 1, ' \
                          '"disk": 2, ' \
                          '"OS-FLV-EXT-DATA:ephemeral": 3, ' \
                          '"swap": 4, ' \
                          '"id": "123", ' \
                          '"flavor_access": [{"id":"1", "name":"test"}]' \
                          '}'

        nc.flavor_create.return_value = mock.Mock(**{
            'id': '1234',
            'to_dict.return_value': {'id': '1234', 'name': 'flavor'}
        })

        flavor_data = {'name': 'flavor',
                       'memory': 12,
                       'vcpu': 1,
                       'disk': 2,
                       'ephemeral': 3,
                       'swap': 4,
                       'flavorid': '123',
                       'is_public': False}

        request = self.mock_rest_request(body=flavor_req_data)
        response = nova.Flavors().post(request)

        self.assertStatusCode(response, 201)
        self.assertEqual(response['location'], '/api/nova/flavors/1234')

        nc.flavor_create.assert_called_once_with(request, **flavor_data)
        nc.add_tenant_to_flavor.assert_called_once_with(request, '1234', '1')

    @mock.patch.object(nova.api, 'nova')
    def test_flavor_update(self, nc):
        flavor_req_data = '{"name": "flavor", ' \
                          '"ram": 12, ' \
                          '"vcpus": 1, ' \
                          '"disk": 2, ' \
                          '"OS-FLV-EXT-DATA:ephemeral": 3, ' \
                          '"swap": 4' \
                          '}'

        nc.flavor_create.return_value = mock.Mock(**{
            'id': '123',
            'to_dict.return_value': {'id': '123', 'name': 'flavor'}
        })

        flavor_data = {'name': 'flavor',
                       'memory': 12,
                       'vcpu': 1,
                       'disk': 2,
                       'ephemeral': 3,
                       'swap': 4,
                       'flavorid': '123',
                       'is_public': True}

        request = self.mock_rest_request(body=flavor_req_data)
        response = nova.Flavor().patch(request, '123')

        self.assertStatusCode(response, 204)

        nc.flavor_delete.assert_called_once_with(request, '123')
        nc.flavor_create.assert_called_once_with(request, **flavor_data)

    @mock.patch.object(nova.api, 'nova')
    def test_flavor_update_with_extras(self, nc):
        flavor_req_data = '{"name": "flavor", ' \
                          '"ram": 12, ' \
                          '"vcpus": 1, ' \
                          '"disk": 2, ' \
                          '"OS-FLV-EXT-DATA:ephemeral": 3, ' \
                          '"swap": 4' \
                          '}'

        extra_dict = mock.Mock()

        nc.flavor_get_extras.return_value = extra_dict

        nc.flavor_create.return_value = mock.Mock(**{
            'id': '1234',
            'to_dict.return_value': {'id': '1234', 'name': 'flavor'}
        })

        flavor_data = {'name': 'flavor',
                       'memory': 12,
                       'vcpu': 1,
                       'disk': 2,
                       'ephemeral': 3,
                       'swap': 4,
                       'flavorid': '123',
                       'is_public': True}

        request = self.mock_rest_request(body=flavor_req_data)
        response = nova.Flavor().patch(request, '123')

        self.assertStatusCode(response, 204)

        nc.flavor_delete.assert_called_once_with(request, '123')
        nc.flavor_create.assert_called_once_with(request, **flavor_data)
        nc.flavor_get_extras.assert_called_once_with(request, '123', raw=True)
        nc.flavor_extra_set.assert_called_once_with(request, '1234',
                                                    extra_dict)

    @mock.patch.object(nova.api, 'nova')
    def test_flavor_update_with_access_list(self, nc):
        flavor_req_data = '{"name": "flavor", ' \
                          '"ram": 12, ' \
                          '"vcpus": 1, ' \
                          '"disk": 2, ' \
                          '"OS-FLV-EXT-DATA:ephemeral": 3, ' \
                          '"swap": 4, ' \
                          '"flavor_access": [{"id":"1", "name":"test"}]' \
                          '}'

        nc.flavor_create.return_value = mock.Mock(**{
            'id': '1234',
            'to_dict.return_value': {'id': '1234', 'name': 'flavor'}
        })

        flavor_data = {'name': 'flavor',
                       'memory': 12,
                       'vcpu': 1,
                       'disk': 2,
                       'ephemeral': 3,
                       'swap': 4,
                       'flavorid': '123',
                       'is_public': False}

        request = self.mock_rest_request(body=flavor_req_data)
        response = nova.Flavor().patch(request, '123')

        self.assertStatusCode(response, 204)

        nc.flavor_delete.assert_called_once_with(request, '123')
        nc.flavor_create.assert_called_once_with(request, **flavor_data)
        nc.add_tenant_to_flavor.assert_called_once_with(request, '1234', '1')

    @mock.patch.object(nova.api, 'nova')
    def _test_flavor_list_public(self, nc, is_public=None):
        if is_public:
            request = self.mock_rest_request(GET={'is_public': 'tRuE'})
        elif is_public is None:
            request = self.mock_rest_request(GET={})
        else:
            request = self.mock_rest_request(GET={'is_public': 'fAlsE'})
        nc.flavor_list.return_value = [
            mock.Mock(**{'to_dict.return_value': {'id': '1'}}),
            mock.Mock(**{'to_dict.return_value': {'id': '2'}}),
        ]
        response = nova.Flavors().get(request)
        self.assertStatusCode(response, 200)
        self.assertEqual(response.json,
                         {"items": [{"id": "1"}, {"id": "2"}]})
        nc.flavor_list.assert_called_once_with(request, is_public=is_public,
                                               get_extras=False)

    def test_flavor_list_private(self):
        self._test_flavor_list_public(is_public=False)

    def test_flavor_list_public(self):
        self._test_flavor_list_public(is_public=True)

    def test_flavor_list_public_none(self):
        self._test_flavor_list_public(is_public=None)

    @mock.patch.object(nova.api, 'nova')
    def _test_flavor_list_extras(self, nc, get_extras=None):
        if get_extras:
            request = self.mock_rest_request(GET={'get_extras': 'tRuE'})
        elif get_extras is None:
            request = self.mock_rest_request(GET={})
            get_extras = False
        else:
            request = self.mock_rest_request(GET={'get_extras': 'fAlsE'})
        nc.flavor_list.return_value = [
            mock.Mock(**{'extras': {}, 'to_dict.return_value': {'id': '1'}}),
            mock.Mock(**{'extras': {}, 'to_dict.return_value': {'id': '2'}}),
        ]
        response = nova.Flavors().get(request)
        self.assertStatusCode(response, 200)
        if get_extras:
            self.assertEqual(response.json,
                             {"items": [{"extras": {}, "id": "1"},
                                        {"extras": {}, "id": "2"}]})
        else:
            self.assertEqual(response.json,
                             {"items": [{"id": "1"}, {"id": "2"}]})
        nc.flavor_list.assert_called_once_with(request, is_public=None,
                                               get_extras=get_extras)

    def test_flavor_list_extras_no(self):
        self._test_flavor_list_extras(get_extras=False)

    def test_flavor_list_extras_yes(self):
        self._test_flavor_list_extras(get_extras=True)

    def test_flavor_list_extras_absent(self):
        self._test_flavor_list_extras(get_extras=None)

    @mock.patch.object(nova.api, 'nova')
    def test_flavor_get_extra_specs(self, nc):
        request = self.mock_rest_request()
        nc.flavor_get_extras.return_value.to_dict.return_value = {'foo': '1'}

        response = nova.FlavorExtraSpecs().get(request, "1")
        self.assertStatusCode(response, 200)
        nc.flavor_get_extras.assert_called_once_with(request, "1", raw=True)

    @mock.patch.object(nova.api, 'nova')
    def test_flavor_edit_extra_specs(self, nc):
        request = self.mock_rest_request(
            body='{"updated": {"a": "1", "b": "2"}, "removed": ["c", "d"]}'
        )

        response = nova.FlavorExtraSpecs().patch(request, '1')
        self.assertStatusCode(response, 204)
        self.assertEqual(response.content, b'')
        nc.flavor_extra_set.assert_called_once_with(
            request, '1', {'a': '1', 'b': '2'}
        )
        nc.flavor_extra_delete.assert_called_once_with(
            request, '1', ['c', 'd']
        )

    @mock.patch.object(nova.api, 'nova')
    def test_aggregate_get_extra_specs(self, nc):
        request = self.mock_rest_request()
        nc.aggregate_get.return_value.metadata = {'a': '1', 'b': '2'}

        response = nova.AggregateExtraSpecs().get(request, "1")
        self.assertStatusCode(response, 200)
        self.assertEqual(response.json, {"a": "1", "b": "2"})
        nc.aggregate_get.assert_called_once_with(request, "1")

    @mock.patch.object(nova.api, 'nova')
    def test_aggregate_edit_extra_specs(self, nc):
        request = self.mock_rest_request(
            body='{"updated": {"a": "1", "b": "2"}, "removed": ["c", "d"]}'
        )

        response = nova.AggregateExtraSpecs().patch(request, '1')
        self.assertStatusCode(response, 204)
        self.assertEqual(response.content, b'')
        nc.aggregate_set_metadata.assert_called_once_with(
            request, '1', {'a': '1', 'b': '2', 'c': None, 'd': None}
        )

    #
    # Services
    #

    @test.create_stubs({api.base: ('is_service_enabled',)})
    @mock.patch.object(nova.api, 'nova')
    def test_services_get(self, nc):
        request = self.mock_rest_request(GET={})
        nc.service_list.return_value = [
            mock.Mock(**{'to_dict.return_value': {'id': '1'}}),
            mock.Mock(**{'to_dict.return_value': {'id': '2'}})
        ]
        api.base.is_service_enabled(request, 'compute').AndReturn(True)

        self.mox.ReplayAll()

        response = nova.Services().get(request)
        self.assertStatusCode(response, 200)
        self.assertEqual(response.content.decode('utf-8'),
                         '{"items": [{"id": "1"}, {"id": "2"}]}')
        nc.service_list.assert_called_once_with(request)

    @test.create_stubs({api.base: ('is_service_enabled',)})
    def test_services_get_disabled(self):
        request = self.mock_rest_request(GET={})

        api.base.is_service_enabled(request, 'compute').AndReturn(False)

        self.mox.ReplayAll()

        response = nova.Services().get(request)
        self.assertStatusCode(response, 501)
