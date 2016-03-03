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
import six

from django.conf import settings
from django.test.utils import override_settings  # noqa

from horizon import exceptions
from openstack_dashboard import api
from openstack_dashboard.test import helpers as test


class HeatApiTests(test.APITestCase):
    def test_stack_list(self):
        api_stacks = self.stacks.list()
        limit = getattr(settings, 'API_RESULT_LIMIT', 1000)

        heatclient = self.stub_heatclient()
        heatclient.stacks = self.mox.CreateMockAnything()
        heatclient.stacks.list(limit=limit,
                               sort_dir='desc',
                               sort_key='created_at',) \
            .AndReturn(iter(api_stacks))
        self.mox.ReplayAll()
        stacks, has_more, has_prev = api.heat.stacks_list(self.request)
        self.assertItemsEqual(stacks, api_stacks)
        self.assertFalse(has_more)
        self.assertFalse(has_prev)

    @override_settings(API_RESULT_PAGE_SIZE=2)
    def test_stack_list_sort_options(self):
        # Verify that sort_dir and sort_key work
        api_stacks = self.stacks.list()
        limit = getattr(settings, 'API_RESULT_LIMIT', 1000)
        sort_dir = 'asc'
        sort_key = 'size'

        heatclient = self.stub_heatclient()
        heatclient.stacks = self.mox.CreateMockAnything()
        heatclient.stacks.list(limit=limit,
                               sort_dir=sort_dir,
                               sort_key=sort_key,) \
            .AndReturn(iter(api_stacks))
        self.mox.ReplayAll()

        stacks, has_more, has_prev = api.heat.stacks_list(self.request,
                                                          sort_dir=sort_dir,
                                                          sort_key=sort_key)
        self.assertItemsEqual(stacks, api_stacks)
        self.assertFalse(has_more)
        self.assertFalse(has_prev)

    @override_settings(API_RESULT_PAGE_SIZE=20)
    def test_stack_list_pagination_less_page_size(self):
        api_stacks = self.stacks.list()
        page_size = settings.API_RESULT_PAGE_SIZE
        sort_dir = 'desc'
        sort_key = 'created_at'

        heatclient = self.stub_heatclient()
        heatclient.stacks = self.mox.CreateMockAnything()
        heatclient.stacks.list(limit=page_size + 1,
                               sort_dir=sort_dir,
                               sort_key=sort_key,) \
            .AndReturn(iter(api_stacks))
        self.mox.ReplayAll()

        stacks, has_more, has_prev = api.heat.stacks_list(self.request,
                                                          sort_dir=sort_dir,
                                                          sort_key=sort_key,
                                                          paginate=True)
        expected_stacks = api_stacks[:page_size]
        self.assertItemsEqual(stacks, expected_stacks)
        self.assertFalse(has_more)
        self.assertFalse(has_prev)

    @override_settings(API_RESULT_PAGE_SIZE=10)
    def test_stack_list_pagination_equal_page_size(self):
        api_stacks = self.stacks.list()
        page_size = settings.API_RESULT_PAGE_SIZE
        sort_dir = 'desc'
        sort_key = 'created_at'

        heatclient = self.stub_heatclient()
        heatclient.stacks = self.mox.CreateMockAnything()
        heatclient.stacks.list(limit=page_size + 1,
                               sort_dir=sort_dir,
                               sort_key=sort_key,) \
            .AndReturn(iter(api_stacks))
        self.mox.ReplayAll()

        stacks, has_more, has_prev = api.heat.stacks_list(self.request,
                                                          sort_dir=sort_dir,
                                                          sort_key=sort_key,
                                                          paginate=True)
        expected_stacks = api_stacks[:page_size]
        self.assertItemsEqual(stacks, expected_stacks)
        self.assertFalse(has_more)
        self.assertFalse(has_prev)

    @override_settings(API_RESULT_PAGE_SIZE=2)
    def test_stack_list_pagination_marker(self):
        page_size = getattr(settings, 'API_RESULT_PAGE_SIZE', 20)
        sort_dir = 'desc'
        sort_key = 'created_at'
        marker = 'nonsense'

        api_stacks = self.stacks.list()

        heatclient = self.stub_heatclient()
        heatclient.stacks = self.mox.CreateMockAnything()
        heatclient.stacks.list(limit=page_size + 1,
                               marker=marker,
                               sort_dir=sort_dir,
                               sort_key=sort_key,) \
            .AndReturn(iter(api_stacks[:page_size + 1]))
        self.mox.ReplayAll()

        stacks, has_more, has_prev = api.heat.stacks_list(self.request,
                                                          marker=marker,
                                                          paginate=True,
                                                          sort_dir=sort_dir,
                                                          sort_key=sort_key,)

        self.assertEqual(len(stacks), page_size)
        self.assertItemsEqual(stacks, api_stacks[:page_size])
        self.assertTrue(has_more)
        self.assertTrue(has_prev)

    @override_settings(API_RESULT_PAGE_SIZE=2)
    def test_stack_list_pagination_marker_prev(self):
        page_size = getattr(settings, 'API_RESULT_PAGE_SIZE', 20)
        sort_dir = 'asc'
        sort_key = 'created_at'
        marker = 'nonsense'

        api_stacks = self.stacks.list()

        heatclient = self.stub_heatclient()
        heatclient.stacks = self.mox.CreateMockAnything()
        heatclient.stacks.list(limit=page_size + 1,
                               marker=marker,
                               sort_dir=sort_dir,
                               sort_key=sort_key,) \
            .AndReturn(iter(api_stacks[:page_size + 1]))
        self.mox.ReplayAll()

        stacks, has_more, has_prev = api.heat.stacks_list(self.request,
                                                          marker=marker,
                                                          paginate=True,
                                                          sort_dir=sort_dir,
                                                          sort_key=sort_key,)

        self.assertEqual(len(stacks), page_size)
        self.assertItemsEqual(stacks, api_stacks[:page_size])
        self.assertTrue(has_more)
        self.assertTrue(has_prev)

    def test_template_get(self):
        api_stacks = self.stacks.list()
        stack_id = api_stacks[0].id
        mock_data_template = self.stack_templates.list()[0]

        heatclient = self.stub_heatclient()
        heatclient.stacks = self.mox.CreateMockAnything()
        heatclient.stacks.template(stack_id).AndReturn(mock_data_template)
        self.mox.ReplayAll()

        template = api.heat.template_get(self.request, stack_id)
        self.assertEqual(mock_data_template.data, template.data)

    def test_stack_create(self):
        api_stacks = self.stacks.list()
        stack = api_stacks[0]

        heatclient = self.stub_heatclient()
        heatclient.stacks = self.mox.CreateMockAnything()
        form_data = {'timeout_mins': 600}
        password = 'secret'
        heatclient.stacks.create(**form_data).AndReturn(stack)
        self.mox.ReplayAll()

        returned_stack = api.heat.stack_create(self.request,
                                               password,
                                               **form_data)
        from heatclient.v1 import stacks
        self.assertIsInstance(returned_stack, stacks.Stack)

    def test_stack_update(self):
        api_stacks = self.stacks.list()
        stack = api_stacks[0]
        stack_id = stack.id

        heatclient = self.stub_heatclient()
        heatclient.stacks = self.mox.CreateMockAnything()
        form_data = {'timeout_mins': 600}
        password = 'secret'
        heatclient.stacks.update(stack_id, **form_data).AndReturn(stack)
        self.mox.ReplayAll()

        returned_stack = api.heat.stack_update(self.request,
                                               stack_id,
                                               password,
                                               **form_data)
        from heatclient.v1 import stacks
        self.assertIsInstance(returned_stack, stacks.Stack)

    def test_snapshot_create(self):
        stack_id = self.stacks.first().id
        snapshot_create = self.stack_snapshot_create.list()[0]

        heatclient = self.stub_heatclient()
        heatclient.stacks = self.mox.CreateMockAnything()
        heatclient.stacks.snapshot(stack_id).AndReturn(snapshot_create)
        self.mox.ReplayAll()

        returned_snapshot_create_info = api.heat.snapshot_create(self.request,
                                                                 stack_id)

        self.assertEqual(returned_snapshot_create_info, snapshot_create)

    def test_snapshot_list(self):
        stack_id = self.stacks.first().id
        snapshot_list = self.stack_snapshot.list()

        heatclient = self.stub_heatclient()
        heatclient.stacks = self.mox.CreateMockAnything()
        heatclient.stacks.snapshot_list(stack_id).AndReturn(snapshot_list)
        self.mox.ReplayAll()

        returned_snapshots = api.heat.snapshot_list(self.request, stack_id)

        self.assertItemsEqual(returned_snapshots, snapshot_list)

    def test_get_template_files_with_template_data(self):
        tmpl = '''
    # comment

    heat_template_version: 2013-05-23
    resources:
      server1:
        type: OS::Nova::Server
        properties:
          flavor: m1.medium
          image: cirros
    '''
        expected_files = {}
        files = api.heat.get_template_files(template_data=tmpl)[0]
        self.assertEqual(files, expected_files)

    def test_get_template_files(self):
        tmpl = '''
    # comment

    heat_template_version: 2013-05-23
    resources:
      server1:
        type: OS::Nova::Server
        properties:
            flavor: m1.medium
            image: cirros
            user_data_format: RAW
            user_data:
              get_file: http://test.example/example
    '''
        expected_files = {u'http://test.example/example': b'echo "test"'}
        url = 'http://test.example/example'
        data = b'echo "test"'
        self.mox.StubOutWithMock(six.moves.urllib.request, 'urlopen')
        six.moves.urllib.request.urlopen(url).AndReturn(
            six.BytesIO(data))
        self.mox.ReplayAll()
        files = api.heat.get_template_files(template_data=tmpl)[0]
        self.assertEqual(files, expected_files)

    def test_get_template_files_with_template_url(self):
        url = 'https://test.example/example.yaml'
        data = b'''
    # comment

    heat_template_version: 2013-05-23
    resources:
      server1:
        type: OS::Nova::Server
        properties:
            flavor: m1.medium
            image: cirros
            user_data_format: RAW
            user_data:
              get_file: http://test.example/example
    '''
        url2 = 'http://test.example/example'
        data2 = b'echo "test"'
        expected_files = {'http://test.example/example': b'echo "test"'}
        self.mox.StubOutWithMock(six.moves.urllib.request, 'urlopen')
        six.moves.urllib.request.urlopen(url).AndReturn(
            six.BytesIO(data))
        six.moves.urllib.request.urlopen(url2).AndReturn(
            six.BytesIO(data2))
        self.mox.ReplayAll()
        files = api.heat.get_template_files(template_url=url)[0]
        self.assertEqual(files, expected_files)

    def test_get_template_files_invalid(self):
        tmpl = '''
    # comment

    heat_template_version: 2013-05-23
    resources:
      server1:
        type: OS::Nova::Server
        properties:
            flavor: m1.medium
            image: cirros
            user_data_format: RAW
            user_data:
              get_file: file:///example
    '''
        try:
            api.heat.get_template_files(template_data=tmpl)[0]
        except exceptions.GetFileError:
            self.assertRaises(exceptions.GetFileError)
