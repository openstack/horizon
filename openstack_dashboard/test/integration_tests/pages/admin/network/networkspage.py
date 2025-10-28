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

from openstack_dashboard.test.integration_tests.pages.project.network \
    import networkspage


class NetworksPage(networkspage.NetworksPage):

    NETWORKS_TABLE_NAME_COLUMN = 'Network Name'

    @property
    def is_admin(self):
        return True

    @property
    def networks_table(self):
        return NetworksTable(self.driver, self.conf)


class NetworksTable(networkspage.NetworksTable):

    CREATE_NETWORK_FORM_FIELDS = (("name", "admin_state",
                                   "with_subnet", "az_hints", "tenant_id",
                                   "network_type"),
                                  ("subnet_name", "cidr", "ip_version",
                                   "gateway_ip", "no_gateway"),
                                  ("enable_dhcp", "allocation_pools",
                                   "dns_nameservers", "host_routes"))
