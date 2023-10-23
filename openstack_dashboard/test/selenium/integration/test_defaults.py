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

import random

import pytest

from openstack_dashboard.test.selenium import widgets


@pytest.fixture
def default_compute_quotas(openstack_admin):
    default_quotas = openstack_admin.compute.get(
        "/os-quota-class-sets/default").json()
    yield None
    openstack_admin.compute.put(
        "/os-quota-class-sets/default",
        json={"quota_class_set":
              {"cores": default_quotas["quota_class_set"]["cores"],
               "instances": default_quotas["quota_class_set"]["instances"],
               }
              })


@pytest.fixture
def default_volume_quotas(openstack_admin):
    default_quotas = openstack_admin.block_storage.get(
        "/os-quota-class-sets/default").json()
    yield None
    openstack_admin.block_storage.put(
        "/os-quota-class-sets/default",
        json={"quota_class_set":
              {"volumes": default_quotas["quota_class_set"]["volumes"],
               "snapshots": default_quotas["quota_class_set"]["snapshots"]
               }
              })


def test_update_compute_defaults(login, driver, openstack_admin, config,
                                 default_compute_quotas):
    number_of_instances = random.randint(101, 10001)
    number_of_cores = random.randint(101, 10001)
    login('admin')
    url = '/'.join((
        config.dashboard.dashboard_url,
        'admin',
        'defaults',
    ))
    driver.get(url)
    driver.find_element_by_link_text("Update Defaults").click()
    defaults_form = driver.find_element_by_css_selector("form .modal-content")
    defaults_form.find_element_by_id("id_instances").clear()
    defaults_form.find_element_by_id("id_instances").send_keys(
        number_of_instances)
    defaults_form.find_element_by_id("id_cores").clear()
    defaults_form.find_element_by_id("id_cores").send_keys(number_of_cores)
    defaults_form.find_element_by_css_selector(".btn-primary").click()
    messages = widgets.get_and_dismiss_messages(driver)
    assert f'Success: Default quotas updated.' in messages
    new_quotas = openstack_admin.compute.get(
        "/os-quota-class-sets/default").json()
    assert(
        new_quotas["quota_class_set"]["instances"] == number_of_instances and
        new_quotas["quota_class_set"]["cores"] == number_of_cores)


def test_update_volume_defaults(login, driver, openstack_admin, config,
                                default_volume_quotas):
    number_of_volumes = random.randint(101, 10001)
    number_of_snapshots = random.randint(101, 10001)
    login('admin')
    url = '/'.join((
        config.dashboard.dashboard_url,
        'admin',
        'defaults',
    ))
    driver.get(url)
    driver.find_element_by_link_text("Volume Quotas").click()
    driver.find_element_by_link_text("Update Defaults").click()
    defaults_form = driver.find_element_by_css_selector("form .modal-content")
    defaults_form.find_element_by_id("id_volumes").clear()
    defaults_form.find_element_by_id("id_volumes").send_keys(number_of_volumes)
    defaults_form.find_element_by_id("id_snapshots").clear()
    defaults_form.find_element_by_id("id_snapshots").send_keys(
        number_of_snapshots)
    defaults_form.find_element_by_css_selector(".btn-primary").click()
    messages = widgets.get_and_dismiss_messages(driver)
    assert f'Success: Default quotas updated.' in messages
    new_quotas = openstack_admin.block_storage.get(
        "/os-quota-class-sets/default").json()
    assert(new_quotas["quota_class_set"]["volumes"] == number_of_volumes and
           new_quotas["quota_class_set"]["snapshots"] == number_of_snapshots)
