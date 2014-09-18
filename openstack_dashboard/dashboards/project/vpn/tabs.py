# Copyright 2013, Mirantis Inc
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
from horizon import tabs

from openstack_dashboard import api

from openstack_dashboard.dashboards.project.vpn import tables


class IPSecSiteConnectionsTab(tabs.TableTab):
    table_classes = (tables.IPSecSiteConnectionsTable,)
    name = _("IPSec Site Connections")
    slug = "ipsecsiteconnections"
    template_name = ("horizon/common/_detail_table.html")

    def get_ipsecsiteconnectionstable_data(self):
        try:
            tenant_id = self.request.user.tenant_id
            ipsecsiteconnections = api.vpn.ipsecsiteconnection_list(
                self.tab_group.request, tenant_id=tenant_id)
        except Exception:
            ipsecsiteconnections = []
            exceptions.handle(
                self.tab_group.request,
                _('Unable to retrieve IPSec Site Connections list.'))
        return ipsecsiteconnections


class VPNServicesTab(tabs.TableTab):
    table_classes = (tables.VPNServicesTable,)
    name = _("VPN Services")
    slug = "vpnservices"
    template_name = ("horizon/common/_detail_table.html")

    def get_vpnservicestable_data(self):
        try:
            tenant_id = self.request.user.tenant_id
            vpnservices = api.vpn.vpnservice_list(
                self.tab_group.request, tenant_id=tenant_id)
        except Exception:
            vpnservices = []
            exceptions.handle(self.tab_group.request,
                              _('Unable to retrieve VPN Services list.'))
        return vpnservices


class IKEPoliciesTab(tabs.TableTab):
    table_classes = (tables.IKEPoliciesTable,)
    name = _("IKE Policies")
    slug = "ikepolicies"
    template_name = ("horizon/common/_detail_table.html")

    def get_ikepoliciestable_data(self):
        try:
            tenant_id = self.request.user.tenant_id
            ikepolicies = api.vpn.ikepolicy_list(
                self.tab_group.request, tenant_id=tenant_id)
        except Exception:
            ikepolicies = []
            exceptions.handle(self.tab_group.request,
                              _('Unable to retrieve IKE Policies list.'))
        return ikepolicies


class IPSecPoliciesTab(tabs.TableTab):
    table_classes = (tables.IPSecPoliciesTable,)
    name = _("IPSec Policies")
    slug = "ipsecpolicies"
    template_name = ("horizon/common/_detail_table.html")

    def get_ipsecpoliciestable_data(self):
        try:
            tenant_id = self.request.user.tenant_id
            ipsecpolicies = api.vpn.ipsecpolicy_list(
                self.tab_group.request, tenant_id=tenant_id)
        except Exception:
            ipsecpolicies = []
            exceptions.handle(self.tab_group.request,
                              _('Unable to retrieve IPSec Policies list.'))
        return ipsecpolicies


class VPNTabs(tabs.TabGroup):
    slug = "vpntabs"
    tabs = (IKEPoliciesTab, IPSecPoliciesTab,
            VPNServicesTab, IPSecSiteConnectionsTab,)
    sticky = True


class IKEPolicyDetailsTab(tabs.Tab):
    name = _("IKE Policy Details")
    slug = "ikepolicydetails"
    template_name = "project/vpn/_ikepolicy_details.html"

    def get_context_data(self, request):
        ikepolicy = self.tab_group.kwargs['ikepolicy']
        return {'ikepolicy': ikepolicy}


class IKEPolicyDetailsTabs(tabs.TabGroup):
    slug = "ikepolicytabs"
    tabs = (IKEPolicyDetailsTab,)


class IPSecPolicyDetailsTab(tabs.Tab):
    name = _("IPSec Policy Details")
    slug = "ipsecpolicydetails"
    template_name = "project/vpn/_ipsecpolicy_details.html"

    def get_context_data(self, request):
        ipsecpolicy = self.tab_group.kwargs['ipsecpolicy']
        return {'ipsecpolicy': ipsecpolicy}


class IPSecPolicyDetailsTabs(tabs.TabGroup):
    slug = "ipsecpolicytabs"
    tabs = (IPSecPolicyDetailsTab,)


class VPNServiceDetailsTab(tabs.Tab):
    name = _("VPN Service Details")
    slug = "vpnservicedetails"
    template_name = "project/vpn/_vpnservice_details.html"

    def get_context_data(self, request):
        vpnservice = self.tab_group.kwargs['vpnservice']
        return {'vpnservice': vpnservice}


class VPNServiceDetailsTabs(tabs.TabGroup):
    slug = "vpnservicetabs"
    tabs = (VPNServiceDetailsTab,)


class IPSecSiteConnectionDetailsTab(tabs.Tab):
    name = _("IPSec Site Connection Details")
    slug = "ipsecsiteconnectiondetails"
    template_name = "project/vpn/_ipsecsiteconnection_details.html"

    def get_context_data(self, request):
        ipsecsiteconnection = self.tab_group.kwargs['ipsecsiteconnection']
        return {'ipsecsiteconnection': ipsecsiteconnection}


class IPSecSiteConnectionDetailsTabs(tabs.TabGroup):
    slug = "ipsecsiteconnectiontabs"
    tabs = (IPSecSiteConnectionDetailsTab,)
