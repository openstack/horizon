# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright 2012 United States Government as represented by the
# Administrator of the National Aeronautics and Space Administration.
# All Rights Reserved.
#
# Copyright 2012 Nebula, Inc.
# Copyright 2012 OpenStack LLC
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

from django.utils.translation import ugettext_lazy as _

from horizon import exceptions
from horizon import messages
from horizon import tabs

from openstack_dashboard.api import keystone
from openstack_dashboard.api import network
from openstack_dashboard.api import nova

from .keypairs.tables import KeypairsTable
from .floating_ips.tables import FloatingIPsTable
from .security_groups.tables import SecurityGroupsTable
from .api_access.tables import EndpointsTable


class SecurityGroupsTab(tabs.TableTab):
    table_classes = (SecurityGroupsTable,)
    name = _("Security Groups")
    slug = "security_groups_tab"
    template_name = "horizon/common/_detail_table.html"

    def get_security_groups_data(self):
        try:
            security_groups = nova.security_group_list(self.request)
        except:
            security_groups = []
            exceptions.handle(self.request,
                              _('Unable to retrieve security groups.'))
        return security_groups


class KeypairsTab(tabs.TableTab):
    table_classes = (KeypairsTable,)
    name = _("Keypairs")
    slug = "keypairs_tab"
    template_name = "horizon/common/_detail_table.html"

    def get_keypairs_data(self):
        try:
            keypairs = nova.keypair_list(self.request)
        except:
            keypairs = []
            exceptions.handle(self.request,
                              _('Unable to retrieve keypair list.'))
        return keypairs


class FloatingIPsTab(tabs.TableTab):
    table_classes = (FloatingIPsTable,)
    name = _("Floating IPs")
    slug = "floating_ips_tab"
    template_name = "horizon/common/_detail_table.html"

    def get_floating_ips_data(self):
        try:
            floating_ips = network.tenant_floating_ip_list(self.request)
        except:
            floating_ips = []
            exceptions.handle(self.request,
                              _('Unable to retrieve floating IP addresses.'))

        try:
            floating_ip_pools = network.floating_ip_pools_list(self.request)
        except:
            floating_ip_pools = []
            messages.warning(self.request,
                             _('Unable to retrieve floating IP pools.'))
        pool_dict = dict([(obj.id, obj.name) for obj in floating_ip_pools])

        instances = []
        try:
            instances = nova.server_list(self.request, all_tenants=True)
        except:
            exceptions.handle(self.request,
                        _('Unable to retrieve instance list.'))

        instances_dict = dict([(obj.id, obj) for obj in instances])

        for ip in floating_ips:
            ip.instance_name = instances_dict[ip.instance_id].name \
                if ip.instance_id in instances_dict else None
            ip.pool_name = pool_dict.get(ip.pool, ip.pool)

        return floating_ips


class APIAccessTab(tabs.TableTab):
    table_classes = (EndpointsTable,)
    name = _("API Access")
    slug = "api_access_tab"
    template_name = "horizon/common/_detail_table.html"

    def get_endpoints_data(self):
        services = []
        for i, service in enumerate(self.request.user.service_catalog):
            service['id'] = i
            services.append(keystone.Service(service))
        return services


class AccessAndSecurityTabs(tabs.TabGroup):
    slug = "access_security_tabs"
    tabs = (SecurityGroupsTab, KeypairsTab, FloatingIPsTab, APIAccessTab)
    sticky = True
