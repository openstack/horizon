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

import os

from openstack_dashboard.test.integration_tests import helpers
from openstack_dashboard.test.integration_tests.regions import messages


class TestMetadataDefinitions(helpers.AdminTestCase):

    NAMESPACE_TEMPLATE_PATH = os.path.join(
        os.path.dirname(__file__),
        'test-data/empty_namespace.json')

    PUBLIC = 'public'
    PROTECTED = 'protected'

    def namespace_create_with_checks(
            self, namespace_name, page, template_json_container,
            expected_namespace_res=None, template_source_type='raw',
            is_public=True, is_protected=False, template_path=None,
            checks=(PUBLIC, PROTECTED)):
        """Create NameSpace and run checks
        :param namespace_name: Display name of namespace in template
        :param page: Connection point
        :param template_json_container: JSON container with NameSpace content
        :param expected_namespace_res: Resources from template
        :param template_source_type: 'raw' or 'file'
        :param is_public: True or False
        :param is_protected: If True- you can't delete it from GUI
        :param checks: Put name of columns if you need to check actual
            representation of 'public' and/or 'protected' value.
            To disable leave it empty: '' OR put None
        :param template_path: Full path to NameSpace template file
        :return: Nothing
        """
        if template_source_type == 'file':
            template_json_container = template_path

        page.import_namespace(
            namespace_json_container=template_json_container,
            is_public=is_public,
            is_protected=is_protected,
            namespace_source_type=template_source_type)
        # Checks
        self.assertTrue(page.find_message_and_dismiss(messages.SUCCESS))
        self.assertFalse(page.find_message_and_dismiss(messages.ERROR))
        self.assertTrue(page.is_namespace_present(namespace_name))
        row = page._get_row_with_namespace_name(namespace_name)
        if checks:
            if self.PUBLIC in checks:
                self.assertTrue(
                    page.is_public_set_correct(namespace_name, is_public, row))
            elif self.PROTECTED in checks:
                self.assertTrue(
                    page.is_protected_set_correct(namespace_name, is_protected,
                                                  row))
        if expected_namespace_res:
            self.assertTrue(page.is_resource_type_set_correct(
                namespace_name, expected_namespace_res, row))

    def namespace_delete_with_checks(self, namespace_name, page):
        """Delete NameSpace and run checks
        :param namespace_name: Display name of namespace in template
        :param page: Connection point
        :return: Nothing
        """
        page.delete_namespace(name=namespace_name)
        # Checks
        self.assertTrue(page.find_message_and_dismiss(messages.SUCCESS))
        self.assertFalse(page.find_message_and_dismiss(messages.ERROR))
        self.assertFalse(page.is_namespace_present(namespace_name))

    def test_namespace_create_delete(self):
        """Tests the NameSpace creation and deletion functionality:
        * Actions:
        * 1) Login to Horizon Dashboard as admin user.
        * 2) Navigate to Admin -> System -> Metadata Definitions.
        * 3) Click "Import Namespace" button. Wait for Create Network dialog.
        * 4) Enter settings for new Namespace:
        *   - Namespace Definition Source: 'raw' or 'file'
        *   - Namespace JSON location;
        *   - Public: Yes  or No;
        *   - Protected: No (check box not enabled).
        * 5) Press "Import Namespace" button.
        * 6) Check that new Namespace was successfully created.
        * 7) Check that new Namespace is present in the table.
        * 8) Check that values in table on page "Metadata Definitions" are
        * the same as in Namespace JSON template and as in step (4):
        *   - Name
        *   - Public
        *   - Protected
        *   - Resource Types
        * 9) Select Namespace in table and press "Delete Namespace" button.
        * 10) In "Confirm Delete Namespace" window press "Delete Namespace".
        * 11) Check that new Namespace was successfully deleted.
        * 12) Check that new Namespace is not present in the table.
        """
        namespaces_page = self.home_pg.go_to_system_metadatadefinitionspage()

        template_json_container = namespaces_page.json_load_template(
            namespace_template_name=self.NAMESPACE_TEMPLATE_PATH)
        # Get name from template file
        namespace_name = template_json_container['display_name']
        # Get resources from template to check representation in GUI
        namespace_res_type = \
            template_json_container['resource_type_associations']
        namespace_res_type = \
            [x['name'] for x in namespace_res_type]

        # Create / Delete NameSpaces with checks
        kwargs = {'namespace_name': namespace_name,
                  'page': namespaces_page,
                  'is_protected': False,
                  'template_json_container': template_json_container,
                  'template_path': self.NAMESPACE_TEMPLATE_PATH}

        self.namespace_create_with_checks(
            template_source_type='raw',
            is_public=True,
            expected_namespace_res=namespace_res_type,
            checks=(self.PUBLIC, self.PROTECTED),
            **kwargs)
        self.namespace_delete_with_checks(namespace_name, namespaces_page)

        self.namespace_create_with_checks(
            template_source_type='raw',
            is_public=False,
            expected_namespace_res=None,
            checks=(self.PUBLIC,),
            **kwargs)
        self.namespace_delete_with_checks(namespace_name, namespaces_page)

        self.namespace_create_with_checks(
            template_source_type='file',
            is_public=True,
            expected_namespace_res=namespace_res_type,
            checks=(self.PUBLIC, self.PROTECTED),
            **kwargs)
        self.namespace_delete_with_checks(namespace_name, namespaces_page)

        self.namespace_create_with_checks(
            template_source_type='file',
            is_public=False,
            expected_namespace_res=None,
            checks=(self.PUBLIC,),
            **kwargs)
        self.namespace_delete_with_checks(namespace_name, namespaces_page)
