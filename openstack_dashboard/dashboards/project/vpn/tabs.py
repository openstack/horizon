# vim: tabstop=4 shiftwidth=4 softtabstop=4

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
#
# @author: Tatiana Mazur


from django.utils.translation import ugettext_lazy as _  # noqa

from horizon import exceptions
from horizon import tabs

from openstack_dashboard import api

from openstack_dashboard.dashboards.project.vpn import tables


class IPSecSiteConnectionsTab(tabs.TableTab):
    table_classes = (tables.IPSecSiteConnectionsTable,)
    name = _("IPSecSiteConnections")
    slug = "ipsecsiteconnections"
    template_name = ("horizon/common/_detail_table.html")

    def get_ipsecsiteconnectionstable_data(self):
        try:
            ipsecsiteconnections = api.vpn.ipsecsiteconnections_get(
                self.tab_group.request)
            ipsecsiteconnectionsFormatted = [s.readable(self.tab_group.request)
                for s in ipsecsiteconnections]
        except Exception:
            ipsecsiteconnectionsFormatted = []
            exceptions.handle(self.tab_group.request,
                _('Unable to retrieve IPSecSiteConnections list.'))
        return ipsecsiteconnectionsFormatted


class VPNServicesTab(tabs.TableTab):
    table_classes = (tables.VPNServicesTable,)
    name = _("VPNServices")
    slug = "vpnservices"
    template_name = ("horizon/common/_detail_table.html")

    def get_vpnservicestable_data(self):
        try:
            vpnservices = api.vpn.vpnservices_get(
                self.tab_group.request)
            vpnservicesFormatted = [s.readable(self.tab_group.request) for
                              s in vpnservices]
        except Exception:
            vpnservicesFormatted = []
            exceptions.handle(self.tab_group.request,
                              _('Unable to retrieve VPNServices list.'))
        return vpnservicesFormatted


class IKEPoliciesTab(tabs.TableTab):
    table_classes = (tables.IKEPoliciesTable,)
    name = _("IKEPolicies")
    slug = "ikepolicies"
    template_name = ("horizon/common/_detail_table.html")

    def get_ikepoliciestable_data(self):
        try:
            ikepolicies = api.vpn.ikepolicies_get(
                self.tab_group.request)
        except Exception:
            ikepolicies = []
            exceptions.handle(self.tab_group.request,
                              _('Unable to retrieve IKEPolicies list.'))
        return ikepolicies


class IPSecPoliciesTab(tabs.TableTab):
    table_classes = (tables.IPSecPoliciesTable,)
    name = _("IPSecPolicies")
    slug = "ipsecpolicies"
    template_name = ("horizon/common/_detail_table.html")

    def get_ipsecpoliciestable_data(self):
        try:
            ipsecpolicies = api.vpn.ipsecpolicies_get(
                self.tab_group.request)
        except Exception:
            ipsecpolicies = []
            exceptions.handle(self.tab_group.request,
                              _('Unable to retrieve IPSecPolicies list.'))
        return ipsecpolicies


class VPNTabs(tabs.TabGroup):
    slug = "vpntabs"
    tabs = (IKEPoliciesTab, IPSecPoliciesTab,
            VPNServicesTab, IPSecSiteConnectionsTab,)
    sticky = True


class IKEPolicyDetailsTab(tabs.Tab):
    name = _("IKEPolicy Details")
    slug = "ikepolicydetails"
    template_name = "project/vpn/_ikepolicy_details.html"

    def get_context_data(self, request):
        pid = self.tab_group.kwargs['ikepolicy_id']
        try:
            ikepolicy = api.vpn.ikepolicy_get(request, pid)
        except Exception:
            ikepolicy = []
            exceptions.handle(request,
                              _('Unable to retrieve IKEPolicy details.'))
        return {'ikepolicy': ikepolicy}


class IKEPolicyDetailsTabs(tabs.TabGroup):
    slug = "ikepolicytabs"
    tabs = (IKEPolicyDetailsTab,)


class IPSecPolicyDetailsTab(tabs.Tab):
    name = _("IPSecPolicy Details")
    slug = "ipsecpolicydetails"
    template_name = "project/vpn/_ipsecpolicy_details.html"

    def get_context_data(self, request):
        pid = self.tab_group.kwargs['ipsecpolicy_id']
        try:
            ipsecpolicy = api.vpn.ipsecpolicy_get(request, pid)
        except Exception:
            ipsecpolicy = []
            exceptions.handle(request,
                              _('Unable to retrieve IPSecPolicy details.'))
        return {'ipsecpolicy': ipsecpolicy}


class IPSecPolicyDetailsTabs(tabs.TabGroup):
    slug = "ipsecpolicytabs"
    tabs = (IPSecPolicyDetailsTab,)


class VPNServiceDetailsTab(tabs.Tab):
    name = _("VPNService Details")
    slug = "vpnservicedetails"
    template_name = "project/vpn/_vpnservice_details.html"

    def get_context_data(self, request):
        sid = self.tab_group.kwargs['vpnservice_id']
        try:
            vpnservice = api.vpn.vpnservice_get(request, sid)
        except Exception:
            vpnservice = []
            exceptions.handle(request,
                              _('Unable to retrieve VPNService details.'))
        return {'vpnservice': vpnservice}


class VPNServiceDetailsTabs(tabs.TabGroup):
    slug = "vpnservicetabs"
    tabs = (VPNServiceDetailsTab,)


class IPSecSiteConnectionDetailsTab(tabs.Tab):
    name = _("IPSecSiteConnection Details")
    slug = "ipsecsiteconnectiondetails"
    template_name = "project/vpn/_ipsecsiteconnection_details.html"

    def get_context_data(self, request):
        cid = self.tab_group.kwargs['ipsecsiteconnection_id']
        try:
            ipsecsiteconnection = api.vpn.ipsecsiteconnection_get(request, cid)
        except Exception:
            ipsecsiteconnection = []
            exceptions.handle(request,
                _('Unable to retrieve IPSecSiteConnection details.'))
        return {'ipsecsiteconnection': ipsecsiteconnection}


class IPSecSiteConnectionDetailsTabs(tabs.TabGroup):
    slug = "ipsecsiteconnectiontabs"
    tabs = (IPSecSiteConnectionDetailsTab,)
