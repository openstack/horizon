# Copyright 2015 IBM Corp.
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

from openstack_dashboard.api.rest import cinder
from openstack_dashboard.test import helpers as test


class CinderRestTestCase(test.TestCase):
    def test_volumes_get(self):
        self._test_volumes_get(False, {})

    def test_volumes_get_all(self):
        self._test_volumes_get(True, {})

    def test_volumes_get_with_filters(self):
        filters = {'status': 'available'}
        self._test_volumes_get(False, filters)

    @mock.patch.object(cinder.api, 'cinder')
    def _test_volumes_get(self, all, filters, cc):
        if all:
            request = self.mock_rest_request(GET={'all_projects': 'true'})
        else:
            request = self.mock_rest_request(**{'GET': filters})
        cc.volume_list.return_value = [
            mock.Mock(**{'to_dict.return_value': {'id': 'one'}}),
            mock.Mock(**{'to_dict.return_value': {'id': 'two'}}),
        ]
        response = cinder.Volumes().get(request)
        self.assertStatusCode(response, 200)
        self.assertEqual(response.json,
                         {"items": [{"id": "one"}, {"id": "two"}]})
        if all:
            cc.volume_list.assert_called_once_with(request,
                                                   {'all_tenants': 1})
        else:
            cc.volume_list.assert_called_once_with(request,
                                                   search_opts=filters)

    @mock.patch.object(cinder.api, 'cinder')
    def test_volume_snaps_get(self, cc):
        request = self.mock_rest_request(**{'GET': {}})
        cc.volume_snapshot_list.return_value = [
            mock.Mock(**{'to_dict.return_value': {'id': 'one'}}),
            mock.Mock(**{'to_dict.return_value': {'id': 'two'}}),
        ]
        response = cinder.VolumeSnapshots().get(request)
        self.assertStatusCode(response, 200)
        self.assertEqual(response.json,
                         {"items": [{"id": "one"}, {"id": "two"}]})
        cc.volume_snapshot_list.assert_called_once_with(request,
                                                        search_opts={})

    @mock.patch.object(cinder.api, 'cinder')
    def test_volume_snaps_get_with_filters(self, cc):
        filters = {'status': 'available'}
        request = self.mock_rest_request(**{'GET': dict(filters)})
        cc.volume_snapshot_list.return_value = [
            mock.Mock(**{'to_dict.return_value': {'id': 'one'}}),
            mock.Mock(**{'to_dict.return_value': {'id': 'two'}}),
        ]
        response = cinder.VolumeSnapshots().get(request)
        self.assertStatusCode(response, 200)
        self.assertEqual(response.json,
                         {"items": [{"id": "one"}, {"id": "two"}]})
        cc.volume_snapshot_list.assert_called_once_with(request,
                                                        search_opts=filters)
