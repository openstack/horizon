# vim: tabstop=4 shiftwidth=4 softtabstop=4

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

from django.conf import settings
from django.test.utils import override_settings  # noqa

from openstack_dashboard import api
from openstack_dashboard.test import helpers as test


class HeatApiTests(test.APITestCase):
    def test_stack_list(self):
        api_stacks = self.stacks.list()
        limit = getattr(settings, 'API_RESULT_LIMIT', 1000)

        heatclient = self.stub_heatclient()
        heatclient.stacks = self.mox.CreateMockAnything()
        heatclient.stacks.list(limit=limit).AndReturn(iter(api_stacks))
        self.mox.ReplayAll()
        stacks, has_more = api.heat.stacks_list(self.request)
        self.assertItemsEqual(stacks, api_stacks)
        self.assertFalse(has_more)

    def test_template_get(self):
        api_stacks = self.stacks.list()
        stack_id = api_stacks[0].id
        mock_data_template = self.stack_templates.list()[0]

        heatclient = self.stub_heatclient()
        heatclient.stacks = self.mox.CreateMockAnything()
        heatclient.stacks.template(stack_id).AndReturn(mock_data_template)
        self.mox.ReplayAll()

        template = api.heat.template_get(self.request, stack_id)
        self.assertEqual(template.data, mock_data_template.data)

    def test_stack_update(self):
        api_stacks = self.stacks.list()
        stack = api_stacks[0]
        stack_id = stack.id

        heatclient = self.stub_heatclient()
        heatclient.stacks = self.mox.CreateMockAnything()
        form_data = {'timeout_mins': 600}
        heatclient.stacks.update(stack_id, **form_data).AndReturn(stack)
        self.mox.ReplayAll()

        returned_stack = api.heat.stack_update(self.request,
                                            stack_id,
                                            **form_data)
        from heatclient.v1 import stacks
        self.assertIsInstance(returned_stack, stacks.Stack)
