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

import openstack as openstack_sdk
from oslo_utils import uuidutils
import pytest

from openstack_dashboard.test.selenium import widgets


@pytest.fixture
def metadata_namespace_name():
    return('horizon_metadata_namespace_%s' %
           uuidutils.generate_uuid(dashed=False))


@pytest.fixture
def new_metadata_namespace(metadata_namespace_name, openstack_admin):
    metadata_namespace = openstack_admin.image.create_metadef_namespace(
        namespace=metadata_namespace_name,
        display_name=metadata_namespace_name,
        description=f"Description for {metadata_namespace_name}")
    yield metadata_namespace
    openstack_admin.image.delete_metadef_namespace(metadata_namespace_name)


@pytest.fixture
def clear_metadata_namespace(metadata_namespace_name, openstack_admin):
    yield None
    openstack_admin.image.delete_metadef_namespace(metadata_namespace_name)


def test_create_metadata_namespace(login, driver, metadata_namespace_name,
                                   config, clear_metadata_namespace,
                                   openstack_admin):
    namespace = str({
        "namespace": f"{metadata_namespace_name}",
        "display_name": f"{metadata_namespace_name}",
        "description": f"Description for {metadata_namespace_name}",
        "resource_type_associations": [
            {
                "name": "OS::Nova::Flavor"
            },
            {
                "name": "OS::Glance::Image"
            }
        ],
        "properties": {
            "prop1": {
                "default": "20",
                "type": "integer",
                "description": "More info here",
                "title": "My property1"
            }
        }
    })
    namespace = namespace.replace("'", '"')

    login('admin')
    url = '/'.join((
        config.dashboard.dashboard_url,
        'admin',
        'metadata_defs',
    ))
    driver.get(url)
    driver.find_element_by_link_text("Import Namespace").click()
    namespace_form = driver.find_element_by_css_selector(".modal-dialog form")
    widgets.select_from_dropdown(namespace_form, "Direct Input")
    namespace_form.find_element_by_id("id_direct_input").send_keys(namespace)
    namespace_form.find_element_by_css_selector(".btn-primary").click()
    messages = widgets.get_and_dismiss_messages(driver)
    assert(f"Success: Namespace {metadata_namespace_name} "
           f"has been created." in messages)
    try:
        openstack_admin.image.get_metadef_namespace(metadata_namespace_name)
        assert True
    except openstack_sdk.exceptions.ResourceNotFound:
        assert False


def test_delete_metadata_namespace(login, driver, new_metadata_namespace,
                                   config, openstack_admin):
    login('admin')
    url = '/'.join((
        config.dashboard.dashboard_url,
        'admin',
        'metadata_defs',
    ))
    driver.get(url)
    rows = driver.find_elements_by_css_selector(
        f"table#namespaces tr[data-display"
        f"='{new_metadata_namespace.namespace}']"
    )
    assert len(rows) == 1
    actions_column = rows[0].find_element_by_css_selector("td.actions_column")
    widgets.select_from_dropdown(actions_column, "Delete Namespace")
    widgets.confirm_modal(driver)
    messages = widgets.get_and_dismiss_messages(driver)
    assert(f"Success: Deleted Namespace: "
           f"{new_metadata_namespace.namespace}" in messages)
    try:
        openstack_admin.image.get_metadef_namespace(
            new_metadata_namespace.namespace)
        assert False
    except openstack_sdk.exceptions.ResourceNotFound:
        assert True
