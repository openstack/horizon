#    (c) Copyright 2014 Hewlett-Packard Development Company, L.P.
#    Copyright 2014 Intel Corporation
#
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


import json

from django.core.urlresolvers import reverse
from django import http

from mox3.mox import IsA  # noqa
import six

from openstack_dashboard import api
from openstack_dashboard.dashboards.admin.metadata_defs \
    import constants
from openstack_dashboard.test import helpers as test


class MetadataDefinitionsView(test.BaseAdminViewTests):

    def test_namespace_object(self):
        mock = self.mox.CreateMockAnything()
        mock.name = 'hello'
        mock.description = 'world'
        mock.visibility = 'public'
        mock.resource_type_associations = [{'name': 'sample'}]

        namespace = api.glance.Namespace(mock)
        self.assertEqual('world', namespace.description)
        self.assertTrue(namespace.public)
        self.assertEqual('sample', namespace.resource_type_names[0])

    @test.create_stubs({api.glance: ('metadefs_namespace_list',)})
    def test_metadata_defs_list(self):
        namespace_list = self.metadata_defs.list()
        api.glance.metadefs_namespace_list(
            IsA(http.HttpRequest),
            sort_dir='asc',
            marker=None,
            paginate=True).AndReturn((namespace_list, False, False))
        self.mox.ReplayAll()

        res = self.client.get(reverse(constants.METADATA_INDEX_URL))
        self.assertTemplateUsed(res, constants.METADATA_INDEX_TEMPLATE)
        self.assertEqual(len(res.context['namespaces_table'].data),
                         len(namespace_list))

    @test.create_stubs({api.glance: ('metadefs_namespace_list',)})
    def test_metadata_defs_no_results(self):
        api.glance.metadefs_namespace_list(
            IsA(http.HttpRequest),
            sort_dir='asc',
            marker=None,
            paginate=True).AndReturn(((), False, False))
        self.mox.ReplayAll()

        res = self.client.get(reverse(constants.METADATA_INDEX_URL))
        self.assertTemplateUsed(res, constants.METADATA_INDEX_TEMPLATE)
        self.assertEqual(len(res.context['namespaces_table'].data), 0)

    @test.create_stubs({api.glance: ('metadefs_namespace_list',)})
    def test_metadata_defs_error(self):
        api.glance.metadefs_namespace_list(
            IsA(http.HttpRequest),
            sort_dir='asc',
            marker=None,
            paginate=True).AndRaise(self.exceptions.glance)
        self.mox.ReplayAll()

        res = self.client.get(reverse(constants.METADATA_INDEX_URL))
        self.assertTemplateUsed(res, constants.METADATA_INDEX_TEMPLATE)

    @test.create_stubs({api.glance: ('metadefs_namespace_list',)})
    def test_delete_availability(self):
        namespace_list = self.metadata_defs.list()
        api.glance.metadefs_namespace_list(
            IsA(http.HttpRequest),
            sort_dir='asc',
            marker=None,
            paginate=True).AndReturn((namespace_list, False, False))
        self.mox.ReplayAll()

        res = self.client.get(reverse(constants.METADATA_INDEX_URL))
        self.assertIn('namespaces_table', res.context)
        ns_table = res.context['namespaces_table']
        namespaces = ns_table.data

        for i in [1, 2]:
            row_actions = ns_table.get_row_actions(namespaces[i])
            self.assertTrue(len(row_actions), 2)
            self.assertTrue('delete' in
                            [a.name for a in row_actions])
            self.assertTrue('manage_resource_types' in
                            [a.name for a in row_actions])

    @test.create_stubs({api.glance: ('metadefs_namespace_get',)})
    def test_metadata_defs_get(self):
        namespace = self.metadata_defs.first()
        api.glance.metadefs_namespace_get(
            IsA(http.HttpRequest),
            '1',
            wrap=True
        ).MultipleTimes().AndReturn(namespace)
        self.mox.ReplayAll()

        res = self.client.get(reverse(constants.METADATA_DETAIL_URL,
                                      kwargs={'namespace_id': '1'}))

        self.assertNoFormErrors(res)
        self.assertTemplateUsed(res, constants.METADATA_DETAIL_TEMPLATE)

    @test.create_stubs({api.glance: ('metadefs_namespace_get',)})
    def test_metadata_defs_get_contents(self):
        namespace = self.metadata_defs.first()
        api.glance.metadefs_namespace_get(
            IsA(http.HttpRequest),
            '1',
            wrap=True
        ).MultipleTimes().AndReturn(namespace)
        self.mox.ReplayAll()

        res = self.client.get(
            '?'.join([reverse(constants.METADATA_DETAIL_URL,
                              kwargs={'namespace_id': '1'}),
                      '='.join(['tab', 'namespace_details__contents'])]))

        self.assertNoFormErrors(res)
        self.assertTemplateUsed(res, constants.METADATA_DETAIL_TEMPLATE)

    @test.create_stubs({api.glance: ('metadefs_namespace_get',)})
    def test_metadata_defs_get_overview(self):
        namespace = self.metadata_defs.first()
        api.glance.metadefs_namespace_get(
            IsA(http.HttpRequest),
            '1',
            wrap=True
        ).MultipleTimes().AndReturn(namespace)
        self.mox.ReplayAll()

        res = self.client.get(
            '?'.join([reverse(constants.METADATA_DETAIL_URL,
                              kwargs={'namespace_id': '1'}),
                      '='.join(['tab', 'namespace_details__overview'])]))

        self.assertNoFormErrors(res)
        self.assertTemplateUsed(res, constants.METADATA_DETAIL_TEMPLATE)

    @test.create_stubs({api.glance: ('metadefs_resource_types_list',
                                     'metadefs_namespace_resource_types')})
    def test_metadata_defs_manage_resource_types(self):
        namespace = self.metadata_defs.first()
        api.glance.metadefs_namespace_resource_types(
            IsA(http.HttpRequest),
            '1'
        ).AndReturn(namespace.resource_type_associations)
        api.glance.metadefs_resource_types_list(
            IsA(http.HttpRequest)
        ).AndReturn(namespace.resource_type_associations)
        self.mox.ReplayAll()

        res = self.client.get(
            reverse(constants.METADATA_MANAGE_RESOURCES_URL,
                    kwargs={'id': '1'}))

        self.assertTemplateUsed(res,
                                constants.METADATA_MANAGE_RESOURCES_TEMPLATE)
        self.assertContains(res, 'mock name')

    @test.create_stubs({api.glance: ('metadefs_namespace_resource_types',
                                     'metadefs_namespace_remove_resource_type',
                                     'metadefs_namespace_add_resource_type')})
    def test_metadata_defs_manage_resource_types_change(self):
        resource_type_associations = [
            {
                'prefix': 'mock1_prefix',
                'name': 'mock1'
            },
            {
                'prefix': 'mock2_prefix',
                'name': 'mock2',
                'selected': True
            }
        ]

        api.glance.metadefs_namespace_resource_types(
            IsA(http.HttpRequest),
            '1'
        ).AndReturn(resource_type_associations)
        api.glance.metadefs_namespace_remove_resource_type(
            IsA(http.HttpRequest),
            '1',
            'mock1'
        ).AndReturn(resource_type_associations)
        api.glance.metadefs_namespace_remove_resource_type(
            IsA(http.HttpRequest),
            '1',
            'mock2'
        ).AndReturn(resource_type_associations)
        api.glance.metadefs_namespace_add_resource_type(
            IsA(http.HttpRequest),
            '1',
            {
                'prefix': 'mock2_prefix',
                'name': 'mock2'
            }
        ).AndReturn(resource_type_associations)
        self.mox.ReplayAll()

        form_data = {'resource_types': json.dumps(resource_type_associations)}
        res = self.client.post(
            reverse(constants.METADATA_MANAGE_RESOURCES_URL,
                    kwargs={'id': '1'}),
            form_data)

        self.assertNoFormErrors(res)
        self.assertMessageCount(success=1)
        self.assertRedirectsNoFollow(
            res, reverse(constants.METADATA_INDEX_URL)
        )


class MetadataDefinitionsCreateViewTest(test.BaseAdminViewTests):

    def test_admin_metadata_defs_create_namespace_get(self):
        res = self.client.get(reverse(constants.METADATA_CREATE_URL))
        self.assertTemplateUsed(res, constants.METADATA_CREATE_TEMPLATE)

    @test.create_stubs({api.glance: ('metadefs_namespace_create',)})
    def test_admin_metadata_defs_create_namespace_post(self):
        metadata = {}
        metadata["namespace"] = "test_namespace"
        metadata["display_name"] = "display_name"
        metadata["description"] = "description"
        metadata["visibility"] = "private"
        metadata["protected"] = False

        api.glance.metadefs_namespace_create(
            IsA(http.HttpRequest),
            metadata
        ).AndReturn(metadata)

        self.mox.ReplayAll()

        form_data = {
            'source_type': 'raw',
            'direct_input': json.dumps(metadata)
        }

        res = self.client.post(reverse(constants.METADATA_CREATE_URL),
                               form_data)

        self.assertNoFormErrors(res)

    def test_admin_metadata_defs_create_namespace_invalid_json_post_raw(self):
        form_data = {
            'source_type': 'raw',
            'direct_input': 'invalidjson'
        }

        res = self.client.post(reverse(constants.METADATA_CREATE_URL),
                               form_data)

        if six.PY3:
            err_msg = ('There was a problem loading the namespace: '
                       'Expecting value: line 1 column 1 (char 0).')
        else:
            err_msg = ('There was a problem loading the namespace: '
                       'No JSON object could be decoded.')
        self.assertFormError(res, "form", None, [err_msg])

    def test_admin_metadata_defs_create_namespace_empty_json_post_raw(self):
        form_data = {
            'source_type': 'raw',
            'direct_input': ''
        }

        res = self.client.post(reverse(constants.METADATA_CREATE_URL),
                               form_data)

        self.assertFormError(res, "form", None, ['No input was provided for '
                                                 'the namespace content.'])

    def test_admin_metadata_defs_create_namespace_empty_json_post_file(self):
        form_data = {
            'source_type': 'raw',
            'direct_input': ''
        }

        res = self.client.post(reverse(constants.METADATA_CREATE_URL),
                               form_data)

        self.assertFormError(res, "form", None, ['No input was provided for '
                                                 'the namespace content.'])
