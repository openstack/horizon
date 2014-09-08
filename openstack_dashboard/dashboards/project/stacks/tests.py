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

from django.conf import settings
from django.core import exceptions
from django.core.urlresolvers import reverse
from django import http
from django.test.utils import override_settings  # noqa
from django.utils import html

from mox import IsA  # noqa

from openstack_dashboard import api
from openstack_dashboard.test import helpers as test

from openstack_dashboard.dashboards.project.stacks import forms
from openstack_dashboard.dashboards.project.stacks import mappings
from openstack_dashboard.dashboards.project.stacks import tables


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

        outputs = ['one', 'two', 'three']
        expected_text = """[\n  "one", \n  "two", \n  "three"\n]"""

        self.assertEqual(u'<pre>%s</pre>' % html.escape(expected_text),
                         mappings.stack_output(outputs))

        outputs = {'foo': 'bar'}
        expected_text = """{\n  "foo": "bar"\n}"""
        self.assertEqual(u'<pre>%s</pre>' % html.escape(expected_text),
                         mappings.stack_output(outputs))

        self.assertEqual(
            u'<a href="http://www.example.com/foo" target="_blank">'
            'http://www.example.com/foo</a>',
            mappings.stack_output('http://www.example.com/foo'))


class StackTests(test.TestCase):

    @override_settings(API_RESULT_PAGE_SIZE=2)
    @test.create_stubs({api.heat: ('stacks_list',)})
    def test_index_paginated(self):
        stacks = self.stacks.list()[:5]

        api.heat.stacks_list(IsA(http.HttpRequest),
                                       marker=None,
                                       paginate=True,
                                       sort_dir='desc') \
                                .AndReturn([stacks,
                                            True, True])
        api.heat.stacks_list(IsA(http.HttpRequest),
                                       marker=None,
                                       paginate=True,
                                       sort_dir='desc') \
                                .AndReturn([stacks[:2],
                                            True, True])
        api.heat.stacks_list(IsA(http.HttpRequest),
                                       marker=stacks[2].id,
                                       paginate=True,
                                       sort_dir='desc') \
                                .AndReturn([stacks[2:4],
                                            True, True])
        api.heat.stacks_list(IsA(http.HttpRequest),
                                       marker=stacks[4].id,
                                       paginate=True,
                                       sort_dir='desc') \
                                .AndReturn([stacks[4:],
                                            True, True])
        self.mox.ReplayAll()

        url = reverse('horizon:project:stacks:index')
        res = self.client.get(url)
        # get all
        self.assertEqual(len(res.context['stacks_table'].data),
                         len(stacks))
        self.assertTemplateUsed(res, 'project/stacks/index.html')

        res = self.client.get(url)
        # get first page with 2 items
        self.assertEqual(len(res.context['stacks_table'].data),
                         settings.API_RESULT_PAGE_SIZE)

        url = "%s?%s=%s" % (reverse('horizon:project:stacks:index'),
                    tables.StacksTable._meta.pagination_param, stacks[2].id)
        res = self.client.get(url)
        # get second page (items 2-4)
        self.assertEqual(len(res.context['stacks_table'].data),
                         settings.API_RESULT_PAGE_SIZE)

        url = "%s?%s=%s" % (reverse('horizon:project:stacks:index'),
                    tables.StacksTable._meta.pagination_param, stacks[4].id)
        res = self.client.get(url)
        # get third page (item 5)
        self.assertEqual(len(res.context['stacks_table'].data),
                         1)

    @override_settings(API_RESULT_PAGE_SIZE=2)
    @test.create_stubs({api.heat: ('stacks_list',)})
    def test_index_prev_paginated(self):
        stacks = self.stacks.list()[:3]

        api.heat.stacks_list(IsA(http.HttpRequest),
                                       marker=None,
                                       paginate=True,
                                       sort_dir='desc') \
                                .AndReturn([stacks,
                                            True, False])
        api.heat.stacks_list(IsA(http.HttpRequest),
                                       marker=None,
                                       paginate=True,
                                       sort_dir='desc') \
                                .AndReturn([stacks[:2],
                                            True, True])
        api.heat.stacks_list(IsA(http.HttpRequest),
                                       marker=stacks[2].id,
                                       paginate=True,
                                       sort_dir='desc') \
                                .AndReturn([stacks[2:],
                                            True, True])
        api.heat.stacks_list(IsA(http.HttpRequest),
                                       marker=stacks[2].id,
                                       paginate=True,
                                       sort_dir='asc') \
                                .AndReturn([stacks[:2],
                                            True, True])
        self.mox.ReplayAll()

        url = reverse('horizon:project:stacks:index')
        res = self.client.get(url)
        # get all
        self.assertEqual(len(res.context['stacks_table'].data),
                         len(stacks))
        self.assertTemplateUsed(res, 'project/stacks/index.html')

        res = self.client.get(url)
        # get first page with 2 items
        self.assertEqual(len(res.context['stacks_table'].data),
                         settings.API_RESULT_PAGE_SIZE)

        url = "%s?%s=%s" % (reverse('horizon:project:stacks:index'),
            tables.StacksTable._meta.pagination_param, stacks[2].id)
        res = self.client.get(url)
        # get second page (item 3)
        self.assertEqual(len(res.context['stacks_table'].data), 1)

        url = "%s?%s=%s" % (reverse('horizon:project:stacks:index'),
            tables.StacksTable._meta.prev_pagination_param, stacks[2].id)
        res = self.client.get(url)
        # prev back to get first page with 2 pages
        self.assertEqual(len(res.context['stacks_table'].data),
                         settings.API_RESULT_PAGE_SIZE)

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
                     'method': forms.CreateStackForm.__name__}
        res = self.client.post(url, form_data)
        self.assertRedirectsNoFollow(res, INDEX_URL)

    @test.create_stubs({api.heat: ('stack_create', 'template_validate')})
    def test_launch_stackwith_environment(self):
        template = self.stack_templates.first()
        environment = self.stack_environments.first()
        stack = self.stacks.first()

        api.heat.template_validate(IsA(http.HttpRequest),
                                   template=template.data,
                                   environment=environment.data) \
           .AndReturn(json.loads(template.validate))

        api.heat.stack_create(IsA(http.HttpRequest),
                              stack_name=stack.stack_name,
                              timeout_mins=60,
                              disable_rollback=True,
                              template=template.data,
                              environment=environment.data,
                              parameters=IsA(dict),
                              password='password')

        self.mox.ReplayAll()

        url = reverse('horizon:project:stacks:select_template')
        res = self.client.get(url)
        self.assertTemplateUsed(res, 'project/stacks/select_template.html')

        form_data = {'template_source': 'raw',
                     'template_data': template.data,
                     'environment_source': 'raw',
                     'environment_data': environment.data,
                     'method': forms.TemplateForm.__name__}
        res = self.client.post(url, form_data)
        self.assertTemplateUsed(res, 'project/stacks/create.html')

        url = reverse('horizon:project:stacks:launch')
        form_data = {'template_source': 'raw',
                     'template_data': template.data,
                     'environment_source': 'raw',
                     'environment_data': environment.data,
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
                     'method': forms.CreateStackForm.__name__}
        res = self.client.post(url, form_data)
        self.assertRedirectsNoFollow(res, INDEX_URL)

    @test.create_stubs({api.heat: ('template_validate',)})
    def test_launch_stack_with_hidden_parameters(self):
        template = {
            'data': ('heat_template_version: 2013-05-23\n'
                     'parameters:\n'
                     '  public_string:\n'
                     '    type: string\n'
                     '  secret_string:\n'
                     '    type: string\n'
                     '    hidden: true\n'),
            'validate': {
                'Description': 'No description',
                'Parameters': {
                    'public_string': {
                        'Label': 'public_string',
                        'Description': '',
                        'Type': 'String',
                        'NoEcho': 'false'
                    },
                    'secret_string': {
                        'Label': 'secret_string',
                        'Description': '',
                        'Type': 'String',
                        'NoEcho': 'true'
                    }
                }
            }
        }
        api.heat.template_validate(IsA(http.HttpRequest),
                                   template=template['data']) \
           .AndReturn(template['validate'])

        self.mox.ReplayAll()

        url = reverse('horizon:project:stacks:select_template')
        res = self.client.get(url)
        self.assertTemplateUsed(res, 'project/stacks/select_template.html')

        form_data = {'template_source': 'raw',
                     'template_data': template['data'],
                     'method': forms.TemplateForm.__name__}
        res = self.client.post(url, form_data)
        self.assertTemplateUsed(res, 'project/stacks/create.html')

        # ensure the fields were rendered correctly
        self.assertContains(res, '<input class="form-control" '
                                        'id="id___param_public_string" '
                                        'name="__param_public_string" '
                                        'type="text" />', html=True)
        self.assertContains(res, '<input class="form-control" '
                                        'id="id___param_secret_string" '
                                        'name="__param_secret_string" '
                                        'type="password" />', html=True)

    @test.create_stubs({api.heat: ('stack_update', 'stack_get',
                                    'template_get', 'template_validate')})
    def test_edit_stack_template(self):
        template = self.stack_templates.first()
        stack = self.stacks.first()

        # GET to template form
        api.heat.stack_get(IsA(http.HttpRequest),
                              stack.id).AndReturn(stack)
        # POST template form, validation
        api.heat.template_validate(IsA(http.HttpRequest),
                                   template=template.data) \
           .AndReturn(json.loads(template.validate))

        # GET to edit form
        api.heat.stack_get(IsA(http.HttpRequest),
                              stack.id).AndReturn(stack)
        api.heat.template_get(IsA(http.HttpRequest),
                              stack.id) \
            .AndReturn(json.loads(template.validate))

        # POST to edit form
        api.heat.stack_get(IsA(http.HttpRequest),
            stack.id).AndReturn(stack)

        fields = {
            'stack_name': stack.stack_name,
            'disable_rollback': True,
            'timeout_mins': 61,
            'password': 'password',
            'template': IsA(unicode),
            'parameters': IsA(dict)
        }
        api.heat.stack_update(IsA(http.HttpRequest),
                              stack_id=stack.id,
                              **fields)
        self.mox.ReplayAll()

        url = reverse('horizon:project:stacks:change_template',
                args=[stack.id])
        res = self.client.get(url)
        self.assertTemplateUsed(res, 'project/stacks/change_template.html')

        form_data = {'template_source': 'raw',
                     'template_data': template.data,
                     'method': forms.ChangeTemplateForm.__name__}
        res = self.client.post(url, form_data)

        url = reverse('horizon:project:stacks:edit_stack',
                args=[stack.id, ])
        form_data = {'template_source': 'raw',
                     'template_data': template.data,
                     'password': 'password',
                     'parameters': template.validate,
                     'stack_name': stack.stack_name,
                     'stack_id': stack.id,
                     "timeout_mins": 61,
                     "disable_rollback": True,
                     "__param_DBUsername": "admin",
                     "__param_LinuxDistribution": "F17",
                     "__param_InstanceType": "m1.small",
                     "__param_KeyName": "test",
                     "__param_DBPassword": "admin",
                     "__param_DBRootPassword": "admin",
                     "__param_DBName": "wordpress",
                     'method': forms.EditStackForm.__name__}
        res = self.client.post(url, form_data)
        self.assertRedirectsNoFollow(res, INDEX_URL)

    def test_launch_stack_form_invalid_names_fail(self):
        self._test_launch_stack_invalid_name('2_StartWithDigit')
        self._test_launch_stack_invalid_name('_StartWithUnderscore')
        self._test_launch_stack_invalid_name('.StartWithPoint')

    def _test_launch_stack_invalid_name(self, name):
        template = self.stack_templates.first()
        url = reverse('horizon:project:stacks:launch')
        form_data = {'template_source': 'raw',
                     'template_data': template.data,
                     'password': 'password',
                     'parameters': template.validate,
                     'stack_name': name,
                     "timeout_mins": 60,
                     "disable_rollback": True,
                     "__param_DBUsername": "admin",
                     "__param_LinuxDistribution": "F17",
                     "__param_InstanceType": "m1.small",
                     "__param_KeyName": "test",
                     "__param_DBPassword": "admin",
                     "__param_DBRootPassword": "admin",
                     "__param_DBName": "wordpress",
                     'method': forms.CreateStackForm.__name__}

        res = self.client.post(url, form_data)
        error = ('Name must start with a letter and may only contain letters, '
                 'numbers, underscores, periods and hyphens.')

        self.assertFormErrors(res, 1)
        self.assertFormError(res, "form", 'stack_name', error)


class TemplateFormTests(test.TestCase):

    class SimpleFile(object):
        def __init__(self, name, data):
            self.name = name
            self.data = data

        def read(self):
            return self.data

    def test_create_upload_form_attributes(self):
        attrs = forms.create_upload_form_attributes(
            'env', 'url', 'Environment')
        self.assertEqual(attrs['data-envsource-url'], 'Environment')

    def test_clean_file_upload_form_url(self):
        kwargs = {'next_view': 'Launch Stack'}
        t = forms.TemplateForm({}, **kwargs)
        precleaned = {
            'template_url': 'http://templateurl.com',
        }
        t.clean_uploaded_files('template', 'template', precleaned, {})

        self.assertEqual(precleaned['template_url'], 'http://templateurl.com')

    def test_clean_file_upload_form_multiple(self):
        kwargs = {'next_view': 'Launch Stack'}
        t = forms.TemplateForm({}, **kwargs)
        precleaned = {
            'template_url': 'http://templateurl.com',
            'template_data': 'http://templateurl.com',
        }
        self.assertRaises(
            exceptions.ValidationError,
            t.clean_uploaded_files,
            'template',
            'template',
            precleaned,
            {})

    def test_clean_file_upload_form_invalid_json(self):
        kwargs = {'next_view': 'Launch Stack'}
        t = forms.TemplateForm({}, **kwargs)
        precleaned = {
            'template_data': 'http://templateurl.com',
        }
        json_str = '{notvalidjson::::::json/////json'
        files = {'template_upload':
            self.SimpleFile('template_name', json_str)}

        self.assertRaises(
            exceptions.ValidationError,
            t.clean_uploaded_files,
            'template',
            'template',
            precleaned,
            files)

    def test_clean_file_upload_form_valid_data(self):
        kwargs = {'next_view': 'Launch Stack'}
        t = forms.TemplateForm({}, **kwargs)
        precleaned = {
            'template_data': 'http://templateurl.com',
        }

        json_str = '{"isvalid":"json"}'
        files = {'template_upload':
            self.SimpleFile('template_name', json_str)}

        t.clean_uploaded_files('template', 'template', precleaned, files)
        self.assertEqual(
            json_str,
            precleaned['template_data'])
