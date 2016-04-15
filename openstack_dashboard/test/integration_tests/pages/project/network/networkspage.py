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

from openstack_dashboard.test.integration_tests.pages import basepage
from openstack_dashboard.test.integration_tests.regions import forms
from openstack_dashboard.test.integration_tests.regions import tables


class NetworksTable(tables.TableRegion):
    name = "networks"
    CREATE_NETWORK_FORM_FIELDS = (("net_name", "admin_state", "shared",
                                   "with_subnet"),
                                  ("subnet_name", "cidr", "ip_version",
                                   "gateway_ip", "no_gateway"),
                                  ("enable_dhcp", "allocation_pools",
                                   "dns_nameservers", "host_routes"))

    @tables.bind_table_action('create')
    def create_network(self, create_button):
        create_button.click()
        return forms.TabbedFormRegion(self.driver, self.conf,
                                      self.CREATE_NETWORK_FORM_FIELDS)

    @tables.bind_table_action('delete')
    def delete_network(self, delete_button):
        delete_button.click()
        return forms.BaseFormRegion(self.driver, self.conf)


class NetworksPage(basepage.BaseNavigationPage):
    DEFAULT_ADMIN_STATE = 'True'
    DEFAULT_CREATE_SUBNET = True
    DEFAULT_IP_VERSION = '4'
    DEFAULT_DISABLE_GATEWAY = False
    DEFAULT_ENABLE_DHCP = True
    NETWORKS_TABLE_NAME_COLUMN = 'name'
    NETWORKS_TABLE_STATUS_COLUMN = 'status'
    SUBNET_TAB_INDEX = 1
    DETAILS_TAB_INDEX = 2

    def __init__(self, driver, conf):
        super(NetworksPage, self).__init__(driver, conf)
        self._page_title = "Networks"

    def _get_row_with_network_name(self, name):
        return self.networks_table.get_row(
            self.NETWORKS_TABLE_NAME_COLUMN, name)

    @property
    def networks_table(self):
        return NetworksTable(self.driver, self.conf)

    def create_network(self, network_name, subnet_name,
                       admin_state=DEFAULT_ADMIN_STATE,
                       create_subnet=DEFAULT_CREATE_SUBNET,
                       network_address=None, ip_version=DEFAULT_IP_VERSION,
                       gateway_ip=None,
                       disable_gateway=DEFAULT_DISABLE_GATEWAY,
                       enable_dhcp=DEFAULT_ENABLE_DHCP, allocation_pools=None,
                       dns_name_servers=None, host_routes=None):
        create_network_form = self.networks_table.create_network()
        create_network_form.net_name.text = network_name
        create_network_form.admin_state.value = admin_state
        if not create_subnet:
            create_network_form.with_subnet.unmark()
        else:
            create_network_form.switch_to(self.SUBNET_TAB_INDEX)
            create_network_form.subnet_name.text = subnet_name
            if network_address is None:
                network_address = self.conf.network.network_cidr
            create_network_form.cidr.text = network_address

            create_network_form.ip_version.value = ip_version
            if gateway_ip is not None:
                create_network_form.gateway_ip.text = gateway_ip
            if disable_gateway:
                create_network_form.disable_gateway.mark()

            create_network_form.switch_to(self.DETAILS_TAB_INDEX)
            if not enable_dhcp:
                create_network_form.enable_dhcp.unmark()
            if allocation_pools is not None:
                create_network_form.allocation_pools.text = allocation_pools
            if dns_name_servers is not None:
                create_network_form.dns_nameservers.text = dns_name_servers
            if host_routes is not None:
                create_network_form.host_routes.text = host_routes
        create_network_form.submit()

    def delete_network(self, name):
        row = self._get_row_with_network_name(name)
        row.mark()
        confirm_delete_networks_form = self.networks_table.delete_network()
        confirm_delete_networks_form.submit()

    def is_network_present(self, name):
        return bool(self._get_row_with_network_name(name))

    def is_network_active(self, name):
        row = self._get_row_with_network_name(name)
        return bool(self.networks_table.wait_cell_status(
            lambda: row.cells[self.NETWORKS_TABLE_STATUS_COLUMN], 'Active'))
