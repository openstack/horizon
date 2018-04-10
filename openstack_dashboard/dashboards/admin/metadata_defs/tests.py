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

from django.urls import reverse

import mock
import six

from openstack_dashboard import api
from openstack_dashboard.dashboards.admin.metadata_defs \
    import constants
from openstack_dashboard.test import helpers as test


class MetadataDefinitionsView(test.BaseAdminViewTests):

    def test_namespace_object(self):
        ns_obj = mock.Mock()
        ns_obj.name = 'hello'
        ns_obj.description = 'world'
        ns_obj.visibility = 'public'
        ns_obj.resource_type_associations = [{'name': 'sample'}]

        namespace = api.glance.Namespace(ns_obj)
        self.assertEqual('world', namespace.description)
        self.assertTrue(namespace.public)
        self.assertEqual('sample', namespace.resource_type_names[0])

    @mock.patch.object(api.glance, 'metadefs_namespace_list')
    def test_metadata_defs_list(self, mock_metafefs_namespace_list):
        namespace_list = self.metadata_defs.list()
        mock_metafefs_namespace_list.return_value = (namespace_list,
                                                     False, False)

        res = self.client.get(reverse(constants.METADATA_INDEX_URL))

        self.assertTemplateUsed(res, constants.METADATA_INDEX_TEMPLATE)
        self.assertEqual(len(res.context['namespaces_table'].data),
                         len(namespace_list))
        mock_metafefs_namespace_list.assert_called_once_with(
            test.IsHttpRequest(), sort_dir='asc',
            marker=None, paginate=True, filters={})

    @mock.patch.object(api.glance, 'metadefs_namespace_list')
    def test_metadata_defs_no_results(self, mock_metadefs_namespace_list):
        mock_metadefs_namespace_list.return_value = ((), False, False)

        res = self.client.get(reverse(constants.METADATA_INDEX_URL))

        self.assertTemplateUsed(res, constants.METADATA_INDEX_TEMPLATE)
        self.assertEqual(len(res.context['namespaces_table'].data), 0)

        mock_metadefs_namespace_list.assert_called_once_with(
            test.IsHttpRequest(), filters={}, marker=None,
            paginate=True, sort_dir='asc')

    @mock.patch.object(api.glance, 'metadefs_namespace_list')
    def test_metadata_defs_error(self, mock_metadefs_namespace_list):
        mock_metadefs_namespace_list.side_effect = self.exceptions.glance

        res = self.client.get(reverse(constants.METADATA_INDEX_URL))

        self.assertTemplateUsed(res, constants.METADATA_INDEX_TEMPLATE)
        mock_metadefs_namespace_list.assert_called_once_with(
            test.IsHttpRequest(), filters={}, marker=None,
            paginate=True, sort_dir='asc')

    @mock.patch.object(api.glance, 'metadefs_namespace_list')
    def test_delete_availability(self, mock_metadefs_namespace_list):
        mock_metadefs_namespace_list.return_value = (self.metadata_defs.list(),
                                                     False, False)

        res = self.client.get(reverse(constants.METADATA_INDEX_URL))
        self.assertIn('namespaces_table', res.context)
        ns_table = res.context['namespaces_table']
        namespaces = ns_table.data

        for i in [1, 2]:
            row_actions = ns_table.get_row_actions(namespaces[i])
            self.assertEqual(len(row_actions), 3)
            self.assertIn('delete',
                          [a.name for a in row_actions])
            self.assertIn('manage_resource_types',
                          [a.name for a in row_actions])

        mock_metadefs_namespace_list.assert_called_once_with(
            test.IsHttpRequest(), sort_dir='asc',
            marker=None, paginate=True, filters={})

    @mock.patch.object(api.glance, 'metadefs_namespace_get')
    def test_metadata_defs_get(self, mock_metadefs_namespace_get):
        mock_metadefs_namespace_get.return_value = self.metadata_defs.first()

        res = self.client.get(reverse(constants.METADATA_DETAIL_URL,
                                      kwargs={'namespace_id': '1'}))

        self.assertNoFormErrors(res)
        self.assertTemplateUsed(res, constants.METADATA_DETAIL_TEMPLATE)

        self.assert_mock_multiple_calls_with_same_arguments(
            mock_metadefs_namespace_get, 2,
            mock.call(test.IsHttpRequest(), '1', wrap=True))

    @mock.patch.object(api.glance, 'metadefs_namespace_get')
    def test_metadata_defs_get_contents(self, mock_metadefs_namespace_get):
        mock_metadefs_namespace_get.return_value = self.metadata_defs.first()

        res = self.client.get(
            '?'.join([reverse(constants.METADATA_DETAIL_URL,
                              kwargs={'namespace_id': '1'}),
                      '='.join(['tab', 'namespace_details__contents'])]))

        self.assertNoFormErrors(res)
        self.assertTemplateUsed(res, constants.METADATA_DETAIL_TEMPLATE)

        self.assert_mock_multiple_calls_with_same_arguments(
            mock_metadefs_namespace_get, 3,
            mock.call(test.IsHttpRequest(), '1', wrap=True))

    @mock.patch.object(api.glance, 'metadefs_namespace_get')
    def test_metadata_defs_get_overview(self, mock_metadefs_namespace_get):
        mock_metadefs_namespace_get.return_value = self.metadata_defs.first()

        res = self.client.get(
            '?'.join([reverse(constants.METADATA_DETAIL_URL,
                              kwargs={'namespace_id': '1'}),
                      '='.join(['tab', 'namespace_details__overview'])]))

        self.assertNoFormErrors(res)
        self.assertTemplateUsed(res, constants.METADATA_DETAIL_TEMPLATE)

        mock_metadefs_namespace_get.assert_has_calls([
            mock.call(test.IsHttpRequest(), '1', wrap=True)])
        self.assertEqual(2, mock_metadefs_namespace_get.call_count)

    @test.create_mocks({api.glance: ['metadefs_resource_types_list',
                                     'metadefs_namespace_resource_types']})
    def test_metadata_defs_manage_resource_types(self):
        namespace = self.metadata_defs.first()
        self.mock_metadefs_resource_types_list.return_value = \
            namespace.resource_type_associations
        self.mock_metadefs_namespace_resource_types.return_value = \
            namespace.resource_type_associations

        res = self.client.get(
            reverse(constants.METADATA_MANAGE_RESOURCES_URL,
                    kwargs={'id': '1'}))

        self.assertTemplateUsed(res,
                                constants.METADATA_MANAGE_RESOURCES_TEMPLATE)
        self.assertContains(res, 'mock name')

        self.mock_metadefs_namespace_resource_types.assert_called_once_with(
            test.IsHttpRequest(), '1')
        self.mock_metadefs_resource_types_list.assert_called_once_with(
            test.IsHttpRequest())

    @test.create_mocks({api.glance: ['metadefs_namespace_resource_types',
                                     'metadefs_namespace_remove_resource_type',
                                     'metadefs_namespace_add_resource_type']})
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
        self.mock_metadefs_namespace_resource_types.return_value = \
            resource_type_associations
        self.mock_metadefs_namespace_remove_resource_type.return_value = \
            resource_type_associations
        self.mock_metadefs_namespace_add_resource_type.return_value = \
            resource_type_associations

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

        self.mock_metadefs_namespace_resource_types.assert_called_once_with(
            test.IsHttpRequest(), '1')
        self.mock_metadefs_namespace_remove_resource_type.assert_has_calls([
            mock.call(test.IsHttpRequest(), '1', 'mock1'),
            mock.call(test.IsHttpRequest(), '1', 'mock2')])
        self.mock_metadefs_namespace_add_resource_type. \
            assert_called_once_with(
                test.IsHttpRequest(), '1',
                {
                    'prefix': 'mock2_prefix',
                    'name': 'mock2'
                })


class MetadataDefinitionsCreateViewTest(test.BaseAdminViewTests):

    def test_admin_metadata_defs_create_namespace_get(self):
        res = self.client.get(reverse(constants.METADATA_CREATE_URL))
        self.assertTemplateUsed(res, constants.METADATA_CREATE_TEMPLATE)

    @mock.patch.object(api.glance, 'metadefs_namespace_create')
    def test_admin_metadata_defs_create_namespace_post(
            self, mock_metadefs_namespace_create):
        metadata = {
            "namespace": "test_namespace",
            "display_name": "display_name",
            "description": "description",
            "visibility": "private",
            "protected": False,
        }

        mock_metadefs_namespace_create.return_value = metadata

        form_data = {
            'source_type': 'raw',
            'direct_input': json.dumps(metadata)
        }

        res = self.client.post(reverse(constants.METADATA_CREATE_URL),
                               form_data)

        self.assertNoFormErrors(res)
        mock_metadefs_namespace_create.assert_called_once_with(
            test.IsHttpRequest(), metadata)

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


class MetadataDefinitionsUpdateViewTest(test.BaseAdminViewTests):

    @mock.patch.object(api.glance, 'metadefs_namespace_get')
    def test_admin_metadata_defs_update_namespace_get(
            self, mock_metadata_namespace_get):
        namespace = self.metadata_defs.first()

        mock_metadata_namespace_get.return_value = namespace

        res = self.client.get(reverse(
            constants.METADATA_UPDATE_URL,
            args=[namespace['namespace']]))
        self.assertTemplateUsed(res, constants.METADATA_UPDATE_TEMPLATE)
        mock_metadata_namespace_get.assert_called_once_with(
            test.IsHttpRequest(), namespace['namespace'])

    @mock.patch.object(api.glance, 'metadefs_namespace_get')
    def test_admin_metadata_defs_update_namespace_get_exception(
            self, mock_metadefs_namespace_get):
        namespace = self.metadata_defs.first()

        mock_metadefs_namespace_get.side_effect = self.exceptions.glance

        res = self.client.get(reverse(
            constants.METADATA_UPDATE_URL,
            args=[namespace['namespace']]))
        self.assertRedirectsNoFollow(res,
                                     reverse(constants.METADATA_INDEX_URL))

        mock_metadefs_namespace_get.assert_called_once_with(
            test.IsHttpRequest(), namespace['namespace'])

    @test.create_mocks({api.glance: ['metadefs_namespace_get',
                                     'metadefs_namespace_update']})
    def test_admin_metadata_defs_update_namespace_post(self):
        namespace = self.metadata_defs.first()
        params = {
            'visibility': namespace.visibility,
            'protected': namespace.protected
        }

        self.mock_metadefs_namespace_update.return_value = namespace
        self.mock_metadefs_namespace_get.return_value = namespace

        form_data = {
            'namespace_id': namespace.namespace,
            'public': True,
            'protected': True
        }

        url = reverse(constants.METADATA_UPDATE_URL,
                      args=[namespace.namespace])
        res = self.client.post(url, form_data)

        self.assertRedirectsNoFollow(res,
                                     reverse(constants.METADATA_INDEX_URL))

        self.mock_metadefs_namespace_update.assert_called_once_with(
            test.IsHttpRequest(), namespace.namespace, **params)
        self.mock_metadefs_namespace_get.assert_called_once_with(
            test.IsHttpRequest(), namespace['namespace'])

    @test.create_mocks({api.glance: ['metadefs_namespace_get',
                                     'metadefs_namespace_update']})
    def test_admin_metadata_defs_update_namespace_post_exception(self):
        namespace = self.metadata_defs.first()
        params = {
            'visibility': namespace.visibility,
            'protected': namespace.protected
        }

        self.mock_metadefs_namespace_update.side_effect = \
            self.exceptions.glance
        self.mock_metadefs_namespace_get.return_value = namespace

        form_data = {
            'namespace_id': namespace.namespace,
            'public': True,
            'protected': True
        }

        url = reverse(constants.METADATA_UPDATE_URL,
                      args=[namespace.namespace])
        res = self.client.post(url, form_data)

        self.assertRedirectsNoFollow(res,
                                     reverse(constants.METADATA_INDEX_URL))

        self.mock_metadefs_namespace_update.assert_called_once_with(
            test.IsHttpRequest(), namespace.namespace, **params)
        self.mock_metadefs_namespace_get.assert_called_once_with(
            test.IsHttpRequest(), namespace['namespace'])
