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

from openstack_dashboard.test.integration_tests.pages import basepage
from openstack_dashboard.test.integration_tests.regions import forms
from openstack_dashboard.test.integration_tests.regions import tables


class MetadatadefinitionsTable(tables.TableRegion):
    name = "namespaces"
    CREATE_NAMESPACE_FORM_FIELDS = (
        "source_type", "direct_input", "metadef_file", "public", "protected")

    @tables.bind_table_action('import')
    def import_namespace(self, create_button):
        create_button.click()
        return forms.FormRegion(
            self.driver,
            self.conf,
            field_mappings=self.CREATE_NAMESPACE_FORM_FIELDS)

    @tables.bind_table_action('delete')
    def delete_namespace(self, delete_button):
        delete_button.click()
        return forms.BaseFormRegion(self.driver, self.conf)


class MetadatadefinitionsPage(basepage.BaseNavigationPage):

    NAMESPACE_TABLE_NAME_COLUMN = 'display_name'
    NAMESPACE_TABLE_DESCRIPTION_COLUMN = 'description'
    NAMESPACE_TABLE_RESOURCE_TYPES_COLUMN = 'resource_type_names'
    NAMESPACE_TABLE_PUBLIC_COLUMN = 'public'
    NAMESPACE_TABLE_PROTECTED_COLUMN = 'protected'

    boolean_mapping = {True: 'Yes', False: 'No'}

    def __init__(self, driver, conf):
        super(MetadatadefinitionsPage, self).__init__(driver, conf)
        self._page_title = "Metadata Definitions"

    def _get_row_with_namespace_name(self, name):
        return self.namespaces_table.get_row(
            self.NAMESPACE_TABLE_NAME_COLUMN,
            name)

    @property
    def namespaces_table(self):
        return MetadatadefinitionsTable(self.driver, self.conf)

    def json_load_template(self, namespace_template_name):
        """Read template for namespace creation

        :param namespace_template_name: Path to template
        :return = json data container
        """
        try:
            with open(namespace_template_name, 'r') as template:
                json_template = json.load(template)
        except Exception:
            raise EOFError("Can not read template file: [{0}]".format(
                namespace_template_name))
        return json_template

    def import_namespace(
            self, namespace_source_type, namespace_json_container,
            is_public=True, is_protected=False):

        create_namespace_form = self.namespaces_table.import_namespace()
        create_namespace_form.source_type.value = namespace_source_type
        if namespace_source_type == 'raw':
            json_template_dump = json.dumps(namespace_json_container)
            create_namespace_form.direct_input.text = json_template_dump
        elif namespace_source_type == 'file':
            metadeffile = namespace_json_container
            create_namespace_form.metadef_file.choose(metadeffile)

        if is_public:
            create_namespace_form.public.mark()
        if is_protected:
            create_namespace_form.protected.mark()

        create_namespace_form.submit()

    def delete_namespace(self, name):
        row = self._get_row_with_namespace_name(name)
        row.mark()
        confirm_delete_namespaces_form = \
            self.namespaces_table.delete_namespace()
        confirm_delete_namespaces_form.submit()

    def is_namespace_present(self, name):
        return bool(self._get_row_with_namespace_name(name))

    def is_public_set_correct(self, name, exp_value, row=None):
        if type(exp_value) != bool:
            raise ValueError('Expected value "exp_value" is not boolean')
        if not row:
            row = self._get_row_with_namespace_name(name)
        cell = row.cells[self.NAMESPACE_TABLE_PUBLIC_COLUMN]
        return self._is_text_visible(cell, self.boolean_mapping[exp_value])

    def is_protected_set_correct(self, name, exp_value, row=None):
        if type(exp_value) != bool:
            raise ValueError('Expected value "exp_value" is not boolean')
        if not row:
            row = self._get_row_with_namespace_name(name)
        cell = row.cells[self.NAMESPACE_TABLE_PROTECTED_COLUMN]
        return self._is_text_visible(cell, self.boolean_mapping[exp_value])

    def is_resource_type_set_correct(self, name, expected_resources, row=None):
        if not row:
            row = self._get_row_with_namespace_name(name)
        cell = row.cells[self.NAMESPACE_TABLE_RESOURCE_TYPES_COLUMN]
        return all(
            [self._is_text_visible(cell, res, strict=False)
             for res in expected_resources])
