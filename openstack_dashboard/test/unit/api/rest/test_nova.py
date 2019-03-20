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

import json
from json import loads as to_json
import uuid

from django.conf import settings
import mock

from openstack_dashboard import api
from openstack_dashboard.api.base import Quota
from openstack_dashboard.api.rest import nova
from openstack_dashboard.test import helpers as test
from openstack_dashboard.usage import quotas


# NOTE(flwang): mock.Mock and mock.MagicMock do not support sort, so the test
# case involved sorted will fail. This fake class is for the flavor test cases
# related to sort.
class FakeFlavor(object):
    def __init__(self, id, ram=1):
        self.id = id
        self.ram = ram
        self.extras = {}

    def to_dict(self):
        return {"id": self.id}


class NovaRestTestCase(test.TestCase):

    #
    # Snapshots
    #
    @test.create_mocks({api.nova: ['snapshot_create']})
    def test_snapshots_create(self):
        body = '{"instance_id": "1234", "name": "foo"}'
        request = self.mock_rest_request(body=body)
        self.mock_snapshot_create.return_value = {'id': 'abcd', 'name': 'foo'}
        response = nova.Snapshots().post(request)
        self.assertStatusCode(response, 200)
        self.assertEqual(response.json, {'id': 'abcd', 'name': 'foo'})
        self.mock_snapshot_create.assert_called_once_with(request,
                                                          instance_id='1234',
                                                          name='foo')

    #
    # Server Actions
    #
    @test.create_mocks({api.nova: ['instance_action_list']})
    def test_serveractions_list(self):
        request = self.mock_rest_request()
        self.mock_instance_action_list.return_value = [
            mock.Mock(**{'to_dict.return_value': {'id': '1'}}),
            mock.Mock(**{'to_dict.return_value': {'id': '2'}}),
        ]
        response = nova.ServerActions().get(request, 'MegaMan')
        self.assertStatusCode(response, 200)
        self.assertEqual(response.json, {'items': [{'id': '1'}, {'id': '2'}]})
        self.mock_instance_action_list.assert_called_once_with(request,
                                                               'MegaMan')

    @test.create_mocks({api.nova: ['server_start']})
    def test_server_start(self):
        self.mock_server_start.return_value = None
        request = self.mock_rest_request(body='{"operation": "start"}')
        response = nova.Server().post(request, 'MegaMan')
        self.assertStatusCode(response, 204)
        self.mock_server_start.assert_called_once_with(request, 'MegaMan')

    @test.create_mocks({api.nova: ['server_stop']})
    def test_server_stop(self):
        self.mock_server_stop.return_value = None
        request = self.mock_rest_request(body='{"operation": "stop"}')
        response = nova.Server().post(request, 'MegaMan')
        self.assertStatusCode(response, 204)
        self.mock_server_stop.assert_called_once_with(request, 'MegaMan')

    @test.create_mocks({api.nova: ['server_pause']})
    def test_server_pause(self):
        self.mock_server_pause.return_value = None
        request = self.mock_rest_request(body='{"operation": "pause"}')
        response = nova.Server().post(request, 'MegaMan')
        self.assertStatusCode(response, 204)
        self.mock_server_pause.assert_called_once_with(request, 'MegaMan')

    @test.create_mocks({api.nova: ['server_unpause']})
    def test_server_unpause(self):
        self.mock_server_unpause.return_value = None
        request = self.mock_rest_request(body='{"operation": "unpause"}')
        response = nova.Server().post(request, 'MegaMan')
        self.assertStatusCode(response, 204)
        self.mock_server_unpause.assert_called_once_with(request, 'MegaMan')

    @test.create_mocks({api.nova: ['server_suspend']})
    def test_server_suspend(self):
        self.mock_server_suspend.return_value = None
        request = self.mock_rest_request(body='{"operation": "suspend"}')
        response = nova.Server().post(request, 'MegaMan')
        self.assertStatusCode(response, 204)
        self.mock_server_suspend.assert_called_once_with(request, 'MegaMan')

    @test.create_mocks({api.nova: ['server_resume']})
    def test_server_resume(self):
        self.mock_server_resume.return_value = None
        request = self.mock_rest_request(body='{"operation": "resume"}')
        response = nova.Server().post(request, 'MegaMan')
        self.assertStatusCode(response, 204)
        self.mock_server_resume.assert_called_once_with(request, 'MegaMan')

    @test.create_mocks({api.nova: ['server_reboot']})
    def test_server_hard_reboot(self):
        self.mock_server_reboot.return_value = None
        request = self.mock_rest_request(body='{"operation": "hard_reboot"}')
        response = nova.Server().post(request, 'MegaMan')
        self.assertStatusCode(response, 204)
        self.mock_server_reboot.assert_called_once_with(request, 'MegaMan',
                                                        False)

    @test.create_mocks({api.nova: ['server_reboot']})
    def test_server_soft_reboot(self):
        self.mock_server_reboot.return_value = None
        request = self.mock_rest_request(body='{"operation": "soft_reboot"}')
        response = nova.Server().post(request, 'MegaMan')
        self.assertStatusCode(response, 204)
        self.mock_server_reboot.assert_called_once_with(request, 'MegaMan',
                                                        True)

    #
    # Security Groups
    #
    @test.create_mocks({api.neutron: ['server_security_groups']})
    def test_securitygroups_list(self):
        request = self.mock_rest_request()
        self.mock_server_security_groups.return_value = [
            mock.Mock(**{'to_dict.return_value': {'id': '1'}}),
            mock.Mock(**{'to_dict.return_value': {'id': '2'}}),
        ]
        response = nova.SecurityGroups().get(request, 'MegaMan')
        self.assertStatusCode(response, 200)
        self.assertEqual(response.json, {'items': [{'id': '1'}, {'id': '2'}]})
        self.mock_server_security_groups.assert_called_once_with(request,
                                                                 'MegaMan')

    #
    # Console Output
    #
    @test.create_mocks({api.nova: ['server_console_output']})
    def test_console_output(self):
        request = self.mock_rest_request(body='{"length": 50}')
        self.mock_server_console_output.return_value = "this\nis\ncool"
        response = nova.ConsoleOutput().post(request, 'MegaMan')
        self.assertStatusCode(response, 200)
        self.assertEqual(response.json, {'lines': ["this", "is", "cool"]})
        self.mock_server_console_output.assert_called_once_with(request,
                                                                'MegaMan',
                                                                tail_length=50)

    #
    # Remote Console Info
    #
    @test.create_mocks({api.nova: ['server_serial_console']})
    def test_console_info(self):
        request = self.mock_rest_request(body='{"console_type": "SERIAL"}')
        retval = mock.Mock(**{"url": "http://here.com"})
        self.mock_server_serial_console.return_value = retval
        response = nova.RemoteConsoleInfo().post(request, 'MegaMan')
        self.assertStatusCode(response, 200)
        self.assertEqual(response.json,
                         {"type": "SERIAL", "url": "http://here.com"})
        self.mock_server_serial_console.assert_called_once_with(request,
                                                                'MegaMan')

    #
    # Volumes
    #
    @test.create_mocks({api.nova: ['instance_volumes_list']})
    def test_volumes_list(self):
        request = self.mock_rest_request()
        self.mock_instance_volumes_list.return_value = [
            mock.Mock(**{'to_dict.return_value': {'id': '1'}}),
            mock.Mock(**{'to_dict.return_value': {'id': '2'}}),
        ]
        response = nova.Volumes().get(request, 'MegaMan')
        self.assertStatusCode(response, 200)
        self.assertEqual(response.json, {'items': [{'id': '1'}, {'id': '2'}]})
        self.mock_instance_volumes_list.assert_called_once_with(request,
                                                                'MegaMan')

    #
    # Keypairs
    #
    @test.create_mocks({api.nova: ['keypair_list']})
    def test_keypair_list(self):
        request = self.mock_rest_request()
        self.mock_keypair_list.return_value = [
            mock.Mock(**{'to_dict.return_value': {'id': 'one'}}),
            mock.Mock(**{'to_dict.return_value': {'id': 'two'}}),
        ]
        response = nova.Keypairs().get(request)
        self.assertStatusCode(response, 200)
        self.assertEqual({"items": [{"id": "one"}, {"id": "two"}]},
                         response.json)
        self.mock_keypair_list.assert_called_once_with(request)

    @test.create_mocks({api.nova: ['keypair_create']})
    def test_keypair_create(self):
        request = self.mock_rest_request(body='''{"name": "Ni!",
                                                  "key_type": "ssh"}''')
        new = self.mock_keypair_create.return_value
        new.to_dict.return_value = {'name': 'Ni!',
                                    'key_type': 'ssh',
                                    'public_key': 'sekrit'}
        new.name = 'Ni!'
        with mock.patch.object(settings, 'DEBUG', True):
            response = nova.Keypairs().post(request)
        self.assertStatusCode(response, 201)
        self.assertEqual({"name": "Ni!",
                          "key_type": "ssh",
                          "public_key": "sekrit"},
                         response.json)
        self.assertEqual('/api/nova/keypairs/Ni%21', response['location'])
        self.mock_keypair_create.assert_called_once_with(request, 'Ni!', 'ssh')

    @test.create_mocks({api.nova: ['keypair_import']})
    def test_keypair_import(self):
        request = self.mock_rest_request(body='''
            {"name": "Ni!", "public_key": "hi", "key_type": "ssh"}
        ''')
        new = self.mock_keypair_import.return_value
        new.to_dict.return_value = {'name': 'Ni!',
                                    'public_key': 'hi',
                                    'key_type': 'ssh'}
        new.name = 'Ni!'
        with mock.patch.object(settings, 'DEBUG', True):
            response = nova.Keypairs().post(request)
        self.assertStatusCode(response, 201)
        self.assertEqual({"name": "Ni!",
                          "public_key": "hi",
                          "key_type": "ssh"},
                         response.json)
        self.assertEqual('/api/nova/keypairs/Ni%21', response['location'])
        self.mock_keypair_import.assert_called_once_with(request,
                                                         'Ni!',
                                                         'hi',
                                                         'ssh')

    @test.create_mocks({api.nova: ['keypair_get']})
    def test_keypair_get(self):
        request = self.mock_rest_request()
        self.mock_keypair_get.return_value.to_dict.return_value = {'name': '1'}
        response = nova.Keypair().get(request, '1')
        self.assertStatusCode(response, 200)
        self.assertEqual({"name": "1"},
                         response.json)
        self.mock_keypair_get.assert_called_once_with(request, "1")

    @test.create_mocks({api.nova: ['keypair_delete']})
    def test_keypair_delete(self):
        self.mock_keypair_delete.return_value = None
        request = self.mock_rest_request()
        nova.Keypair().delete(request, "1")
        self.mock_keypair_delete.assert_called_once_with(request, "1")

    #
    # Availability Zones
    #
    def test_availzone_get_brief(self):
        self._test_availzone_get(False)

    def test_availzone_get_detailed(self):
        self._test_availzone_get(True)

    @test.create_mocks({api.nova: ['availability_zone_list']})
    def _test_availzone_get(self, detail):
        if detail:
            request = self.mock_rest_request(GET={'detailed': 'true'})
        else:
            request = self.mock_rest_request(GET={})
        self.mock_availability_zone_list.return_value = [
            mock.Mock(**{'to_dict.return_value': {'id': 'one'}}),
            mock.Mock(**{'to_dict.return_value': {'id': 'two'}}),
        ]
        response = nova.AvailabilityZones().get(request)
        self.assertStatusCode(response, 200)
        self.assertEqual({"items": [{"id": "one"}, {"id": "two"}]},
                         response.json)
        self.mock_availability_zone_list.assert_called_once_with(request,
                                                                 detail)

    #
    # Limits
    #
    def test_limits_get_not_reserved(self):
        self._test_limits_get(False)

    def test_limits_get_reserved(self):
        self._test_limits_get(True)

    @test.create_mocks({api.nova: ['tenant_absolute_limits']})
    def _test_limits_get(self, reserved):
        if reserved:
            request = self.mock_rest_request(GET={'reserved': 'true'})
        else:
            request = self.mock_rest_request(GET={})
        self.mock_tenant_absolute_limits.return_value = {'id': 'one'}
        response = nova.Limits().get(request)
        self.assertStatusCode(response, 200)
        self.mock_tenant_absolute_limits.assert_called_once_with(request,
                                                                 reserved)
        self.assertEqual({"id": "one"}, response.json)

    #
    # Servers
    #
    def test_server_create_missing(self):
        request = self.mock_rest_request(body='''{"name": "hi"}''')
        response = nova.Servers().post(request)
        self.assertStatusCode(response, 400)
        self.assertEqual("missing required parameter 'source_id'",
                         response.json)

    @test.create_mocks({api.nova: ['server_create']})
    def test_server_create_basic(self):
        request = self.mock_rest_request(body='''{"name": "Ni!",
            "source_id": "image123", "flavor_id": "flavor123",
            "key_name": "sekrit", "user_data": "base64 yes",
            "security_groups": [{"name": "root"}]}
        ''')
        new = self.mock_server_create.return_value
        new.to_dict.return_value = {'id': 'server123'}
        new.id = 'server123'
        response = nova.Servers().post(request)
        self.assertStatusCode(response, 201)
        self.assertEqual({"id": "server123"}, response.json)
        self.assertEqual('/api/nova/servers/server123', response['location'])
        self.mock_server_create.assert_called_once_with(
            request, 'Ni!', 'image123', 'flavor123', 'sekrit', 'base64 yes',
            [{'name': 'root'}]
        )

    @test.create_mocks({api.nova: ['server_create']})
    def test_server_create_with_leading_trailing_space(self):
        request = self.mock_rest_request(body='''{"name": " Ni! ",
                "source_id": "image123", "flavor_id": "flavor123",
                "key_name": "sekrit", "user_data": "base64 yes",
                "security_groups": [{"name": "root"}]}
            ''')
        new = self.mock_server_create.return_value
        new.to_dict.return_value = {'name': ' Ni! '.strip()}
        new.id = str(uuid.uuid4())
        response = nova.Servers().post(request)
        self.assertStatusCode(response, 201)
        self.assertEqual({"name": "Ni!"}, response.json)
        self.mock_server_create.assert_called_once_with(
            request, ' Ni! ', 'image123', 'flavor123', 'sekrit', 'base64 yes',
            [{'name': 'root'}])

    @test.create_mocks({api.nova: ['server_list']})
    def test_server_list(self):
        request = self.mock_rest_request()
        self.mock_server_list.return_value = ([
            mock.Mock(**{'to_dict.return_value': {'id': 'one'}}),
            mock.Mock(**{'to_dict.return_value': {'id': 'two'}}),
        ], False)

        response = nova.Servers().get(request)
        self.assertStatusCode(response, 200)
        self.assertEqual({'items': [{'id': 'one'}, {'id': 'two'}]},
                         response.json)
        self.mock_server_list.assert_called_once_with(request)

    @test.create_mocks({api.nova: ['server_get']})
    def test_server_get_single(self):
        request = self.mock_rest_request()
        self.mock_server_get.return_value.to_dict.return_value = {'name': '1'}

        response = nova.Server().get(request, "1")
        self.assertStatusCode(response, 200)
        self.mock_server_get.assert_called_once_with(request, "1")

    #
    # Server Groups
    #
    @test.create_mocks({api.nova: ['server_group_list']})
    def test_server_group_list(self):
        request = self.mock_rest_request()
        self.mock_server_group_list.return_value = [
            mock.Mock(**{'to_dict.return_value': {'id': '1'}}),
            mock.Mock(**{'to_dict.return_value': {'id': '2'}}),
        ]

        response = nova.ServerGroups().get(request)
        self.assertStatusCode(response, 200)
        self.assertEqual({'items': [{'id': '1'}, {'id': '2'}]},
                         response.json)
        self.mock_server_group_list.assert_called_once_with(request)

    @test.create_mocks({api.nova: ['server_group_create']})
    def test_server_group_create(self):
        req_data = json.dumps({
            'name': 'server_group', 'policies': ['affinity']})

        self.mock_server_group_create.return_value = mock.Mock(**{
            'id': '123',
            'to_dict.return_value': {'id': '123',
                                     'name': 'server_group',
                                     'policies': ['affinity']}
        })

        server_group_data = {'name': 'server_group',
                             'policies': ['affinity']}
        request = self.mock_rest_request(body=req_data)
        response = nova.ServerGroups().post(request)

        self.assertStatusCode(response, 201)
        self.assertEqual('/api/nova/servergroups/123', response['location'])

        self.mock_server_group_create.assert_called_once_with(
            request, **server_group_data)

    @test.create_mocks({api.nova: ['server_group_delete']})
    def test_server_group_delete(self):
        request = self.mock_rest_request()
        self.mock_server_group_delete.return_value = None
        nova.ServerGroup().delete(request, "1")
        self.mock_server_group_delete.assert_called_once_with(request, "1")

    @test.create_mocks({api.nova: ['server_group_get']})
    def test_server_group_get_single(self):
        request = self.mock_rest_request()
        servergroup = self.server_groups.first()
        self.mock_server_group_get.return_value = servergroup

        response = nova.ServerGroup().get(request, "1")

        self.assertStatusCode(response, 200)
        self.assertEqual(servergroup.to_dict(), response.json)
        self.mock_server_group_get.assert_called_once_with(request, "1")

    #
    # Server Metadata
    #
    @test.create_mocks({api.nova: ['server_get']})
    def test_server_get_metadata(self):
        request = self.mock_rest_request()
        meta = {'foo': 'bar'}
        ret_val_server = self.mock_server_get.return_value
        ret_val_server.to_dict.return_value.get.return_value = meta

        response = nova.ServerMetadata().get(request, "1")
        self.assertStatusCode(response, 200)
        self.mock_server_get.assert_called_once_with(request, "1")

    @test.create_mocks({api.nova: ['server_metadata_delete',
                                   'server_metadata_update']})
    def test_server_edit_metadata(self):
        request = self.mock_rest_request(
            body='{"updated": {"a": "1", "b": "2"}, "removed": ["c", "d"]}'
        )
        self.mock_server_metadata_update.return_value = None
        self.mock_server_metadata_delete.return_value = None

        response = nova.ServerMetadata().patch(request, '1')
        self.assertStatusCode(response, 204)
        self.assertEqual(b'', response.content)
        self.mock_server_metadata_update.assert_called_once_with(
            request, '1', {'a': '1', 'b': '2'}
        )
        self.mock_server_metadata_delete.assert_called_once_with(
            request, '1', ['c', 'd']
        )

    #
    # Extensions
    #
    @test.create_mocks({api.nova: ['list_extensions']})
    @mock.patch.object(settings,
                       'OPENSTACK_NOVA_EXTENSIONS_BLACKLIST', ['baz'])
    def _test_extension_list(self):
        request = self.mock_rest_request()
        self.mock_list_extensions.return_value = [
            mock.Mock(**{'to_dict.return_value': {'name': 'foo'}}),
            mock.Mock(**{'to_dict.return_value': {'name': 'bar'}}),
            mock.Mock(**{'to_dict.return_value': {'name': 'baz'}}),
        ]
        response = nova.Extensions().get(request)
        self.assertStatusCode(response, 200)
        self.assertEqual({"items": [{"name": "foo"}, {"name": "bar"}]},
                         response.json)
        self.mock_list_extensions.assert_called_once_with(request)

    #
    # Flavors
    #

    @test.create_mocks({api.nova: ['flavor_get', 'flavor_access_list']})
    def test_flavor_get_single_with_access_list(self):
        request = self.mock_rest_request(GET={'get_access_list': 'tRuE'})
        self.mock_flavor_get.return_value.to_dict.return_value = {'name': '1'}
        self.mock_flavor_get.return_value.is_public = False

        self.mock_flavor_access_list.return_value = [
            mock.Mock(**{'tenant_id': '11'}),
            mock.Mock(**{'tenant_id': '22'}),
        ]

        response = nova.Flavor().get(request, "1")

        self.assertStatusCode(response, 200)
        self.assertEqual(to_json(response.content.decode('utf-8')),
                         to_json('{"access-list": ["11", "22"], "name": "1"}'))

        self.mock_flavor_get.assert_called_once_with(request, "1",
                                                     get_extras=False)
        self.mock_flavor_access_list.assert_called_once_with(request, "1")

    def test_get_extras_no(self):
        self._test_flavor_get_single(get_extras=False)

    def test_get_extras_yes(self):
        self._test_flavor_get_single(get_extras=True)

    def test_get_extras_default(self):
        self._test_flavor_get_single(get_extras=None)

    @test.create_mocks({api.nova: ['flavor_get']})
    def _test_flavor_get_single(self, get_extras):
        if get_extras:
            request = self.mock_rest_request(GET={'get_extras': 'tRuE'})
        elif get_extras is None:
            request = self.mock_rest_request()
            get_extras = False
        else:
            request = self.mock_rest_request(GET={'get_extras': 'fAlsE'})
        self.mock_flavor_get.return_value.to_dict.return_value = {'name': '1'}

        response = nova.Flavor().get(request, "1")
        self.assertStatusCode(response, 200)
        if get_extras:
            self.assertEqual(response.json, {"extras": {}, "name": "1"})
        else:
            self.assertEqual({"name": "1"}, response.json)
        self.mock_flavor_get.assert_called_once_with(request, "1",
                                                     get_extras=get_extras)

    @test.create_mocks({api.nova: ['flavor_get']})
    def test_flavor_get_single_with_swap_set_to_empty(self):
        request = self.mock_rest_request()
        self.mock_flavor_get.return_value\
            .to_dict.return_value = {'name': '1', 'swap': ''}

        response = nova.Flavor().get(request, "1")

        self.assertStatusCode(response, 200)
        self.assertEqual(to_json(response.content.decode('utf-8')),
                         to_json('{"name": "1", "swap": 0}'))
        self.mock_flavor_get.assert_called_once_with(request, '1',
                                                     get_extras=False)

    @test.create_mocks({api.nova: ['flavor_delete']})
    def test_flavor_delete(self):
        self.mock_flavor_delete.return_value = None
        request = self.mock_rest_request()
        nova.Flavor().delete(request, "1")
        self.mock_flavor_delete.assert_called_once_with(request, "1")

    @test.create_mocks({api.nova: ['flavor_create']})
    def test_flavor_create(self):
        flavor_req_data = '{"name": "flavor", ' \
                          '"ram": 12, ' \
                          '"vcpus": 1, ' \
                          '"disk": 2, ' \
                          '"OS-FLV-EXT-DATA:ephemeral": 3, ' \
                          '"swap": 4, ' \
                          '"id": "123"' \
                          '}'

        self.mock_flavor_create.return_value = mock.Mock(**{
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
        self.assertEqual('/api/nova/flavors/123', response['location'])

        self.mock_flavor_create.assert_called_once_with(request, **flavor_data)

    @test.create_mocks({api.nova: ['flavor_create',
                                   'add_tenant_to_flavor']})
    def test_flavor_create_with_access_list(self):
        flavor_req_data = '{"name": "flavor", ' \
                          '"ram": 12, ' \
                          '"vcpus": 1, ' \
                          '"disk": 2, ' \
                          '"OS-FLV-EXT-DATA:ephemeral": 3, ' \
                          '"swap": 4, ' \
                          '"id": "123", ' \
                          '"flavor_access": [{"id":"1", "name":"test"}]' \
                          '}'

        self.mock_flavor_create.return_value = mock.Mock(**{
            'id': '1234',
            'to_dict.return_value': {'id': '1234', 'name': 'flavor'}
        })
        # A list of FlavorAccess object is returned but it is actually unused.
        self.mock_add_tenant_to_flavor.return_value = [
            mock.sentinel.flavor_access1,
        ]

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
        self.assertEqual('/api/nova/flavors/1234', response['location'])

        self.mock_flavor_create.assert_called_once_with(request, **flavor_data)
        self.mock_add_tenant_to_flavor.assert_called_once_with(
            request, '1234', '1')

    @test.create_mocks({api.nova: ['flavor_create',
                                   'flavor_delete',
                                   'flavor_get_extras']})
    def test_flavor_update(self):
        flavor_req_data = '{"name": "flavor", ' \
                          '"ram": 12, ' \
                          '"vcpus": 1, ' \
                          '"disk": 2, ' \
                          '"OS-FLV-EXT-DATA:ephemeral": 3, ' \
                          '"swap": 4' \
                          '}'

        self.mock_flavor_get_extras.return_value = {}
        self.mock_flavor_create.return_value = mock.Mock(**{
            'id': '123',
            'to_dict.return_value': {'id': '123', 'name': 'flavor'}
        })
        self.mock_flavor_delete.return_value = None

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

        self.mock_flavor_get_extras.assert_called_once_with(
            request, '123', raw=True)
        self.mock_flavor_delete.assert_called_once_with(request, '123')
        self.mock_flavor_create.assert_called_once_with(request, **flavor_data)

    @test.create_mocks({api.nova: ['flavor_create', 'flavor_delete',
                                   'flavor_extra_set', 'flavor_get_extras']})
    def test_flavor_update_with_extras(self):
        flavor_req_data = '{"name": "flavor", ' \
                          '"ram": 12, ' \
                          '"vcpus": 1, ' \
                          '"disk": 2, ' \
                          '"OS-FLV-EXT-DATA:ephemeral": 3, ' \
                          '"swap": 4' \
                          '}'

        extra_dict = mock.Mock()

        self.mock_flavor_get_extras.return_value = extra_dict
        self.mock_flavor_create.return_value = mock.Mock(**{
            'id': '1234',
            'to_dict.return_value': {'id': '1234', 'name': 'flavor'}
        })
        self.mock_flavor_delete.return_value = None
        self.mock_flavor_extra_set.return_value = None

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

        self.mock_flavor_delete.assert_called_once_with(request, '123')
        self.mock_flavor_create.assert_called_once_with(request, **flavor_data)
        self.mock_flavor_get_extras.assert_called_once_with(request, '123',
                                                            raw=True)
        self.mock_flavor_extra_set.assert_called_once_with(request, '1234',
                                                           extra_dict)

    @test.create_mocks({api.nova: ['flavor_create',
                                   'flavor_delete',
                                   'flavor_get_extras',
                                   'add_tenant_to_flavor']})
    def test_flavor_update_with_access_list(self):
        flavor_req_data = '{"name": "flavor", ' \
                          '"ram": 12, ' \
                          '"vcpus": 1, ' \
                          '"disk": 2, ' \
                          '"OS-FLV-EXT-DATA:ephemeral": 3, ' \
                          '"swap": 4, ' \
                          '"flavor_access": [{"id":"1", "name":"test"}]' \
                          '}'

        self.mock_flavor_get_extras.return_value = {}
        self.mock_flavor_create.return_value = mock.Mock(**{
            'id': '1234',
            'to_dict.return_value': {'id': '1234', 'name': 'flavor'}
        })
        self.mock_flavor_delete.return_value = None
        # A list of FlavorAccess object is returned but it is actually unused.
        self.mock_add_tenant_to_flavor.return_value = [
            mock.sentinel.flavor_access1,
        ]

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

        self.mock_flavor_get_extras.assert_called_once_with(
            request, '123', raw=True)
        self.mock_flavor_delete.assert_called_once_with(request, '123')
        self.mock_flavor_create.assert_called_once_with(request, **flavor_data)
        self.mock_add_tenant_to_flavor.assert_called_once_with(
            request, '1234', '1')

    @test.create_mocks({api.nova: ['flavor_list']})
    def _test_flavor_list_public(self, is_public=None):
        if is_public:
            request = self.mock_rest_request(GET={'is_public': 'tRuE'})
        elif is_public is None:
            request = self.mock_rest_request(GET={})
        else:
            request = self.mock_rest_request(GET={'is_public': 'fAlsE'})
        self.mock_flavor_list.return_value = [
            FakeFlavor("1"), FakeFlavor("2")
        ]
        response = nova.Flavors().get(request)
        self.assertStatusCode(response, 200)
        self.assertEqual({"items": [{"id": "1"}, {"id": "2"}]},
                         response.json)
        self.mock_flavor_list.assert_called_once_with(request,
                                                      is_public=is_public,
                                                      get_extras=False)

    def test_flavor_list_private(self):
        self._test_flavor_list_public(is_public=False)

    def test_flavor_list_public(self):
        self._test_flavor_list_public(is_public=True)

    def test_flavor_list_public_none(self):
        self._test_flavor_list_public(is_public=None)

    @test.create_mocks({api.nova: ['flavor_list']})
    def _test_flavor_list_extras(self, get_extras=None):
        if get_extras:
            request = self.mock_rest_request(GET={'get_extras': 'tRuE'})
        elif get_extras is None:
            request = self.mock_rest_request(GET={})
            get_extras = False
        else:
            request = self.mock_rest_request(GET={'get_extras': 'fAlsE'})

        self.mock_flavor_list.return_value = [
            FakeFlavor("1"), FakeFlavor("2")
        ]
        response = nova.Flavors().get(request)
        self.assertStatusCode(response, 200)
        if get_extras:
            self.assertEqual({"items": [{"extras": {}, "id": "1"},
                                        {"extras": {}, "id": "2"}]},
                             response.json)
        else:
            self.assertEqual({"items": [{"id": "1"}, {"id": "2"}]},
                             response.json)
        self.mock_flavor_list.assert_called_once_with(request, is_public=None,
                                                      get_extras=get_extras)

    def test_flavor_list_extras_no(self):
        self._test_flavor_list_extras(get_extras=False)

    def test_flavor_list_extras_yes(self):
        self._test_flavor_list_extras(get_extras=True)

    def test_flavor_list_extras_absent(self):
        self._test_flavor_list_extras(get_extras=None)

    @test.create_mocks({api.nova: ['flavor_get_extras']})
    def test_flavor_get_extra_specs(self):
        request = self.mock_rest_request()
        self.mock_flavor_get_extras.return_value.to_dict.return_value = \
            {'foo': '1'}

        response = nova.FlavorExtraSpecs().get(request, "1")
        self.assertStatusCode(response, 200)
        self.mock_flavor_get_extras.assert_called_once_with(request, "1",
                                                            raw=True)

    @test.create_mocks({api.nova: ['flavor_extra_delete',
                                   'flavor_extra_set']})
    def test_flavor_edit_extra_specs(self):
        request = self.mock_rest_request(
            body='{"updated": {"a": "1", "b": "2"}, "removed": ["c", "d"]}'
        )
        self.mock_flavor_extra_delete.return_value = None
        self.mock_flavor_extra_set.return_value = {'a': '1', 'b': '2'}

        response = nova.FlavorExtraSpecs().patch(request, '1')
        self.assertStatusCode(response, 204)
        self.assertEqual(b'', response.content)
        self.mock_flavor_extra_set.assert_called_once_with(
            request, '1', {'a': '1', 'b': '2'}
        )
        self.mock_flavor_extra_delete.assert_called_once_with(
            request, '1', ['c', 'd']
        )

    @test.create_mocks({api.nova: ['aggregate_get']})
    def test_aggregate_get_extra_specs(self):
        request = self.mock_rest_request()
        self.mock_aggregate_get.return_value.metadata = {'a': '1', 'b': '2'}

        response = nova.AggregateExtraSpecs().get(request, "1")
        self.assertStatusCode(response, 200)
        self.assertEqual({"a": "1", "b": "2"}, response.json)
        self.mock_aggregate_get.assert_called_once_with(request, "1")

    @test.create_mocks({api.nova: ['aggregate_set_metadata']})
    def test_aggregate_edit_extra_specs(self):
        self.mock_aggregate_set_metadata.return_value = self.aggregates.first()
        request = self.mock_rest_request(
            body='{"updated": {"a": "1", "b": "2"}, "removed": ["c", "d"]}'
        )

        response = nova.AggregateExtraSpecs().patch(request, '1')
        self.assertStatusCode(response, 204)
        self.assertEqual(b'', response.content)
        self.mock_aggregate_set_metadata.assert_called_once_with(
            request, '1', {'a': '1', 'b': '2', 'c': None, 'd': None}
        )

    #
    # Services
    #

    @test.create_mocks({api.base: ['is_service_enabled'],
                        api.nova: ['service_list',
                                   'extension_supported']})
    def test_services_get(self):
        request = self.mock_rest_request(GET={})
        self.mock_service_list.return_value = [
            mock.Mock(**{'to_dict.return_value': {'id': '1'}}),
            mock.Mock(**{'to_dict.return_value': {'id': '2'}})
        ]
        self.mock_is_service_enabled.return_value = True
        self.mock_extension_supported.return_value = True

        response = nova.Services().get(request)

        self.assertStatusCode(response, 200)
        self.assertEqual('{"items": [{"id": "1"}, {"id": "2"}]}',
                         response.content.decode('utf-8'))
        self.mock_service_list.assert_called_once_with(request)
        self.mock_is_service_enabled.assert_called_once_with(request,
                                                             'compute')
        self.mock_extension_supported.assert_called_once_with(
            'Services', request)

    @mock.patch.object(api.base, 'is_service_enabled')
    def test_services_get_disabled(self, mock_is_service_enabled):
        request = self.mock_rest_request(GET={})
        mock_is_service_enabled.return_value = False

        response = nova.Services().get(request)

        self.assertStatusCode(response, 501)
        mock_is_service_enabled.assert_called_once_with(request, 'compute')

    @test.create_mocks({api.base: ['is_service_enabled'],
                        quotas: ['get_disabled_quotas'],
                        api.nova: ['default_quota_get']})
    def test_quota_sets_defaults_get(self):
        filters = {'user': {'tenant_id': 'tenant'}}
        request = self.mock_rest_request(**{'GET': dict(filters)})

        self.mock_is_service_enabled.return_value = True
        self.mock_get_disabled_quotas.return_value = ['floating_ips']
        self.mock_default_quota_get.return_value = [
            Quota('metadata_items', 100),
            Quota('floating_ips', 1),
            Quota('q2', 101)
        ]

        response = nova.DefaultQuotaSets().get(request)
        self.assertStatusCode(response, 200)
        self.assertEqual(response.json,
                         {"items": [
                             {"limit": 100,
                              "display_name": "Metadata Items",
                              "name": "metadata_items"},
                             {"limit": 101,
                              "display_name": "Q2",
                              "name": "q2"}
                         ]})

        self.mock_is_service_enabled.assert_called_once_with(request,
                                                             'compute')
        self.mock_get_disabled_quotas.assert_called_once_with(request)
        self.mock_default_quota_get.assert_called_once_with(
            request, request.user.tenant_id)

    @test.create_mocks({api.base: ['is_service_enabled']})
    def test_quota_sets_defaults_get_when_service_is_disabled(self):
        filters = {'user': {'tenant_id': 'tenant'}}
        request = self.mock_rest_request(**{'GET': dict(filters)})
        self.mock_is_service_enabled.return_value = False

        response = nova.DefaultQuotaSets().get(request)

        self.assertStatusCode(response, 501)
        self.assertEqual(response.content.decode('utf-8'),
                         '"Service Nova is disabled."')
        self.mock_is_service_enabled.assert_called_once_with(request,
                                                             'compute')

    @test.create_mocks({api.base: ['is_service_enabled'],
                        quotas: ['get_disabled_quotas'],
                        api.nova: ['default_quota_update']})
    def test_quota_sets_defaults_patch(self):
        request = self.mock_rest_request(body='''
            {"key_pairs": "15", "metadata_items": "5000",
            "cores": "10", "instances": "20", "floating_ips": 10,
            "injected_file_content_bytes": "15",
            "injected_file_path_bytes": "5000",
            "injected_files": "5", "ram": "10", "gigabytes": "5"}
        ''')

        self.mock_is_service_enabled.return_value = True
        self.mock_get_disabled_quotas.return_value = ['floating_ips']
        self.mock_default_quota_update.return_value = None

        response = nova.DefaultQuotaSets().patch(request)

        self.assertStatusCode(response, 204)
        self.assertEqual(response.content.decode('utf-8'), '')

        self.mock_is_service_enabled.assert_called_once_with(request,
                                                             'compute')
        self.mock_get_disabled_quotas.assert_called_once_with(request)
        self.mock_default_quota_update.assert_called_once_with(
            request, key_pairs='15',
            metadata_items='5000', cores='10',
            instances='20', injected_file_content_bytes='15',
            injected_file_path_bytes='5000',
            injected_files='5', ram='10')

    @test.create_mocks({api.base: ['is_service_enabled']})
    def test_quota_sets_defaults_patch_when_service_is_disabled(self):
        request = self.mock_rest_request(body='''
            {"key_pairs": "15", "metadata_items": "5000",
            "cores": "10", "instances": "20", "floating_ips": 10,
            "injected_file_content_bytes": "15",
            "injected_file_path_bytes": "5000",
            "injected_files": "5", "ram": "10", "gigabytes": "5"}
        ''')

        self.mock_is_service_enabled.return_value = False

        response = nova.DefaultQuotaSets().patch(request)

        self.assertStatusCode(response, 501)
        self.assertEqual(response.content.decode('utf-8'),
                         '"Service Nova is disabled."')

        self.mock_is_service_enabled.assert_called_once_with(request,
                                                             'compute')

    @test.create_mocks({quotas: ['get_disabled_quotas']})
    def test_editable_quotas_get(self):
        disabled_quotas = {'floating_ips', 'fixed_ips',
                           'security_groups', 'security_group_rules'}
        editable_quotas = {'cores', 'volumes', 'network', 'fixed_ips'}
        self.mock_get_disabled_quotas.return_value = disabled_quotas
        request = self.mock_rest_request()

        with mock.patch.object(quotas, 'QUOTA_FIELDS', editable_quotas):
            response = nova.EditableQuotaSets().get(request)

        self.assertStatusCode(response, 200)
        # NOTE(amotoki): assertItemsCollectionEqual cannot be used below
        # since the item list is generated from a set and the order of items
        # is unpredictable.
        self.assertEqual(set(response.json['items']),
                         {'cores', 'volumes', 'network'})
        self.mock_get_disabled_quotas.assert_called_once_with(request)

    @test.create_mocks({api.base: ['is_service_enabled'],
                        quotas: ['get_disabled_quotas'],
                        api.nova: ['tenant_quota_update']})
    def test_quota_sets_patch(self):
        quota_data = dict(cores='15', instances='5',
                          ram='50000', metadata_items='150',
                          injected_files='5',
                          injected_file_content_bytes='10240',
                          floating_ips='50', fixed_ips='5',
                          security_groups='10',
                          security_group_rules='100')

        request = self.mock_rest_request(body='''
            {"cores": "15", "ram": "50000", "instances": "5",
             "metadata_items": "150", "injected_files": "5",
             "injected_file_content_bytes": "10240", "floating_ips": "50",
             "fixed_ips": "5", "security_groups": "10" ,
             "security_group_rules": "100", "volumes": "10"}
        ''')

        self.mock_get_disabled_quotas.return_value = set()
        self.mock_is_service_enabled.return_value = True
        self.mock_tenant_quota_update.return_value = None

        with mock.patch.object(quotas, 'NOVA_QUOTA_FIELDS',
                               {n for n in quota_data}):
            response = nova.QuotaSets().patch(request, 'spam123')

        self.assertStatusCode(response, 204)
        self.assertEqual(response.content.decode('utf-8'), '')
        self.mock_is_service_enabled.assert_called_once_with(request,
                                                             'compute')
        self.mock_get_disabled_quotas.assert_called_once_with(request)
        self.mock_tenant_quota_update.assert_called_once_with(
            request, 'spam123', **quota_data)

    @test.create_mocks({api.nova: ['tenant_quota_update'],
                        api.base: ['is_service_enabled'],
                        quotas: ['get_disabled_quotas']})
    def test_quota_sets_patch_when_service_is_disabled(self):
        quota_data = dict(cores='15', instances='5',
                          ram='50000', metadata_items='150',
                          injected_files='5',
                          injected_file_content_bytes='10240',
                          floating_ips='50', fixed_ips='5',
                          security_groups='10',
                          security_group_rules='100')

        request = self.mock_rest_request(body='''
            {"cores": "15", "ram": "50000", "instances": "5",
             "metadata_items": "150", "injected_files": "5",
             "injected_file_content_bytes": "10240", "floating_ips": "50",
             "fixed_ips": "5", "security_groups": "10" ,
             "security_group_rules": "100", "volumes": "10"}
        ''')

        self.mock_get_disabled_quotas.return_value = {}
        self.mock_is_service_enabled.return_value = False
        self.mock_tenant_quota_update.return_value = None

        with mock.patch.object(quotas, 'NOVA_QUOTA_FIELDS',
                               {n for n in quota_data}):
            response = nova.QuotaSets().patch(request, 'spam123')

        self.assertStatusCode(response, 501)
        self.assertEqual(response.content.decode('utf-8'),
                         '"Service Nova is disabled."')
        self.mock_get_disabled_quotas.assert_called_once_with(request)
        self.mock_is_service_enabled.assert_called_once_with(request,
                                                             'compute')
        self.mock_tenant_quota_update.assert_not_called()

    @test.create_mocks({api.nova: ['is_feature_available']})
    def test_version_get(self):
        request = self.mock_rest_request()
        self.mock_is_feature_available.return_value = True

        response = nova.Features().get(request, 'fake')
        self.assertStatusCode(response, 200)
        self.assertEqual(response.content.decode('utf-8'), 'true')
        self.mock_is_feature_available.assert_called_once_with(request,
                                                               ('fake',))
