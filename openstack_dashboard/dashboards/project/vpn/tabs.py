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


from django.core.urlresolvers import reverse_lazy  # noqa
from django.utils.translation import ugettext_lazy as _  # noqa

from horizon import exceptions
from horizon import tabs

from openstack_dashboard import api

from openstack_dashboard.dashboards.project.vpn import tables


def get_resource_or_fake(request, base_obj, resource, api_module):
    """Return a resource detail or a fake object if it fails.

    This methods retrieves a specified resource of base_obj.
    It gets the resource ID from base_obj.<resource>_id and then
    calls api_module.<resource>_get(resource_id).
    If the api call fails, it returns a fake object which contains
    only resource_id for the specified resouce.
    The retrieved object is set to base_obj.<resource>.
    """
    obj_id = getattr(base_obj, '%s_id' % resource)
    try:
        obj_getter = getattr(api_module, '%s_get' % resource)
        obj = obj_getter(request, obj_id)
        setattr(base_obj, resource, obj)
    except Exception:
        fake_dict = {'id': obj_id, 'name': ''}
        setattr(base_obj, resource,
                api.neutron.NeutronAPIDictWrapper(fake_dict))


class IPSecSiteConnectionsTab(tabs.TableTab):
    table_classes = (tables.IPSecSiteConnectionsTable,)
    name = _("IPSec Site Connections")
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
                _('Unable to retrieve IPSec Site Connections list.'))
        return ipsecsiteconnectionsFormatted


class VPNServicesTab(tabs.TableTab):
    table_classes = (tables.VPNServicesTable,)
    name = _("VPN Services")
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
                              _('Unable to retrieve VPN Services list.'))
        return vpnservicesFormatted


class IKEPoliciesTab(tabs.TableTab):
    table_classes = (tables.IKEPoliciesTable,)
    name = _("IKE Policies")
    slug = "ikepolicies"
    template_name = ("horizon/common/_detail_table.html")

    def get_ikepoliciestable_data(self):
        try:
            ikepolicies = api.vpn.ikepolicies_get(
                self.tab_group.request)
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
            ipsecpolicies = api.vpn.ipsecpolicies_get(
                self.tab_group.request)
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
    failure_url = reverse_lazy('horizon:project:vpn:index')

    def get_context_data(self, request):
        pid = self.tab_group.kwargs['ikepolicy_id']
        try:
            ikepolicy = api.vpn.ikepolicy_get(request, pid)
        except Exception:
            msg = _('Unable to retrieve IKE Policy details.')
            exceptions.handle(request, msg, redirect=self.failure_url)
        return {'ikepolicy': ikepolicy}


class IKEPolicyDetailsTabs(tabs.TabGroup):
    slug = "ikepolicytabs"
    tabs = (IKEPolicyDetailsTab,)


class IPSecPolicyDetailsTab(tabs.Tab):
    name = _("IPSec Policy Details")
    slug = "ipsecpolicydetails"
    template_name = "project/vpn/_ipsecpolicy_details.html"
    failure_url = reverse_lazy('horizon:project:vpn:index')

    def get_context_data(self, request):
        pid = self.tab_group.kwargs['ipsecpolicy_id']
        try:
            ipsecpolicy = api.vpn.ipsecpolicy_get(request, pid)
        except Exception:
            msg = _('Unable to retrieve IPSec Policy details.')
            exceptions.handle(request, msg, redirect=self.failure_url)
        return {'ipsecpolicy': ipsecpolicy}


class IPSecPolicyDetailsTabs(tabs.TabGroup):
    slug = "ipsecpolicytabs"
    tabs = (IPSecPolicyDetailsTab,)


class VPNServiceDetailsTab(tabs.Tab):
    name = _("VPN Service Details")
    slug = "vpnservicedetails"
    template_name = "project/vpn/_vpnservice_details.html"
    failure_url = reverse_lazy('horizon:project:vpn:index')

    def get_context_data(self, request):
        sid = self.tab_group.kwargs['vpnservice_id']
        try:
            vpnservice = api.vpn.vpnservice_get(request, sid)
        except Exception:
            msg = _('Unable to retrieve VPN Service details.')
            exceptions.handle(request, msg, redirect=self.failure_url)
        try:
            connections = api.vpn.ipsecsiteconnections_get(
                request, vpnservice_id=sid)
            vpnservice.vpnconnections = connections
        except Exception:
            vpnservice.vpnconnections = []

        get_resource_or_fake(request, vpnservice, 'router', api.neutron)
        get_resource_or_fake(request, vpnservice, 'subnet', api.neutron)
        return {'vpnservice': vpnservice}


class VPNServiceDetailsTabs(tabs.TabGroup):
    slug = "vpnservicetabs"
    tabs = (VPNServiceDetailsTab,)


class IPSecSiteConnectionDetailsTab(tabs.Tab):
    name = _("IPSec Site Connection Details")
    slug = "ipsecsiteconnectiondetails"
    template_name = "project/vpn/_ipsecsiteconnection_details.html"
    failure_url = reverse_lazy('horizon:project:vpn:index')

    def get_context_data(self, request):
        cid = self.tab_group.kwargs['ipsecsiteconnection_id']
        try:
            ipsecsiteconn = api.vpn.ipsecsiteconnection_get(request, cid)
        except Exception:
            msg = _('Unable to retrieve IPSec Site Connection details.')
            exceptions.handle(request, msg, redirect=self.failure_url)

        get_resource_or_fake(request, ipsecsiteconn, 'vpnservice', api.vpn)
        get_resource_or_fake(request, ipsecsiteconn, 'ipsecpolicy', api.vpn)
        get_resource_or_fake(request, ipsecsiteconn, 'ikepolicy', api.vpn)
        return {'ipsecsiteconnection': ipsecsiteconn}


class IPSecSiteConnectionDetailsTabs(tabs.TabGroup):
    slug = "ipsecsiteconnectiontabs"
    tabs = (IPSecSiteConnectionDetailsTab,)
