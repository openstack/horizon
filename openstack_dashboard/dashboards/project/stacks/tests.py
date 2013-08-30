# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

import json

from django.core.urlresolvers import reverse  # noqa
from django import http

from mox import IsA  # noqa

from openstack_dashboard import api
from openstack_dashboard.test import helpers as test

from openstack_dashboard.dashboards.project.stacks import forms
from openstack_dashboard.dashboards.project.stacks import mappings


INDEX_URL = reverse('horizon:project:stacks:index')


class MockResource(object):
    def __init__(self, resource_type, physical_resource_id):
        self.resource_type = resource_type
        self.physical_resource_id = physical_resource_id


class MappingsTests(test.TestCase):

    def test_mappings(self):

        def assertMappingUrl(url, resource_type, physical_resource_id):
            mock = MockResource(resource_type, physical_resource_id)
            mock_url = mappings.resource_to_url(mock)
            self.assertEqual(url, mock_url)

        assertMappingUrl(
            '/project/networks/subnets/aaa/detail',
            'OS::Quantum::Subnet',
            'aaa')
        assertMappingUrl(
            None,
            'OS::Quantum::Subnet',
            None)
        assertMappingUrl(
            None,
            None,
            None)
        assertMappingUrl(
            None,
            'AWS::AutoScaling::LaunchConfiguration',
            'aaa')
        assertMappingUrl(
            '/project/instances/aaa/',
            'AWS::EC2::Instance',
            'aaa')
        assertMappingUrl(
            '/project/containers/aaa/',
            'OS::Swift::Container',
            'aaa')
        assertMappingUrl(
            None,
            'Foo::Bar::Baz',
            'aaa')

    def test_stack_output(self):
        self.assertEqual(u'foo', mappings.stack_output('foo'))
        self.assertEqual(u'', mappings.stack_output(None))

        self.assertEqual(
            u'<pre>[\n  "one", \n  "two", \n  "three"\n]</pre>',
            mappings.stack_output(['one', 'two', 'three']))
        self.assertEqual(
            u'<pre>{\n  "foo": "bar"\n}</pre>',
            mappings.stack_output({'foo': 'bar'}))

        self.assertEqual(
            u'<a href="http://www.example.com/foo" target="_blank">'
            'http://www.example.com/foo</a>',
            mappings.stack_output('http://www.example.com/foo'))


class StackTests(test.TestCase):

    @test.create_stubs({api.heat: ('stacks_list',)})
    def test_index(self):
        stacks = self.stacks.list()

        api.heat.stacks_list(IsA(http.HttpRequest)) \
           .AndReturn(stacks)
        self.mox.ReplayAll()

        res = self.client.get(INDEX_URL)

        self.assertTemplateUsed(res, 'project/stacks/index.html')
        self.assertIn('table', res.context)
        resp_stacks = res.context['table'].data
        self.assertEqual(len(resp_stacks), len(stacks))

    @test.create_stubs({api.heat: ('stack_create', 'template_validate')})
    def test_launch_stack(self):
        template = self.stack_templates.first()
        stack = self.stacks.first()

        api.heat.template_validate(IsA(http.HttpRequest),
                                   template=template.data) \
           .AndReturn(json.loads(template.validate))

        api.heat.stack_create(IsA(http.HttpRequest),
                              stack_name=stack.stack_name,
                              timeout_mins=60,
                              disable_rollback=True,
                              template=template.data,
                              parameters=IsA(dict),
                              password='password')

        self.mox.ReplayAll()

        url = reverse('horizon:project:stacks:select_template')
        res = self.client.get(url)
        self.assertTemplateUsed(res, 'project/stacks/select_template.html')

        form_data = {'template_source': 'raw',
                     'template_data': template.data,
                     'method': forms.TemplateForm.__name__}
        res = self.client.post(url, form_data)
        self.assertTemplateUsed(res, 'project/stacks/create.html')

        url = reverse('horizon:project:stacks:launch')
        form_data = {'template_source': 'raw',
                     'template_data': template.data,
                     'password': 'password',
                     'parameters': template.validate,
                     'stack_name': stack.stack_name,
                     "timeout_mins": 60,
                     "disable_rollback": True,
                     "__param_DBUsername": "admin",
                     "__param_LinuxDistribution": "F17",
                     "__param_InstanceType": "m1.small",
                     "__param_KeyName": "test",
                     "__param_DBPassword": "admin",
                     "__param_DBRootPassword": "admin",
                     "__param_DBName": "wordpress",
                     'method': forms.StackCreateForm.__name__}
        res = self.client.post(url, form_data)
        self.assertRedirectsNoFollow(res, INDEX_URL)


class TemplateFormTests(test.TestCase):

    def test_exception_to_validation(self):
        json_error = """{
    "code": 400,
    "error": {
        "message": "The Key (none) could not be found.",
        "traceback": "<Traceback>",
        "type": "StackValidationFailed"
    },
    "explanation": "The server could not comply with the request",
    "title": "Bad Request"
}"""

        msg = forms.exception_to_validation_msg(json_error)
        self.assertEqual(msg, "The Key (none) could not be found.")

    def test_exception_to_validation_legacy(self):
        json_error = """400 Bad Request

The server could not comply with the request since it is either \
malformed or otherwise incorrect.

 Remote error: StackValidationFailed The Key (none) could not be found. \
[u'<Traceback>']."""

        msg = forms.exception_to_validation_msg(json_error)
        self.assertEqual(msg, "The Key (none) could not be found.")

    def test_exception_to_validation_malformed(self):
        json_error = """{
    "code": 400,
    "error": {
        "traceback": "<Traceback>",
        "type": "StackValidationFailed"
    },
    "explanation": "The server could not comply with the request",
    "title": "Bad Request"
}"""

        msg = forms.exception_to_validation_msg(json_error)
        self.assertEqual(msg, None)
