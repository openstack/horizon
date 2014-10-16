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

from django.conf.urls import patterns
from django.conf.urls import url

from openstack_dashboard.dashboards.project.vpn import views

urlpatterns = patterns(
    'openstack_dashboard.dashboards.project.vpn.views',
    url(r'^$', views.IndexView.as_view(), name='index'),
    url(r'^addikepolicy$',
        views.AddIKEPolicyView.as_view(), name='addikepolicy'),
    url(r'^update_ikepolicy/(?P<ikepolicy_id>[^/]+)/$',
        views.UpdateIKEPolicyView.as_view(), name='update_ikepolicy'),
    url(r'^addipsecpolicy$',
        views.AddIPSecPolicyView.as_view(), name='addipsecpolicy'),
    url(r'^update_ipsecpolicy/(?P<ipsecpolicy_id>[^/]+)/$',
        views.UpdateIPSecPolicyView.as_view(), name='update_ipsecpolicy'),
    url(r'^addipsecsiteconnection$',
        views.AddIPSecSiteConnectionView.as_view(),
        name='addipsecsiteconnection'),
    url(r'^update_ipsecsiteconnection/(?P<ipsecsiteconnection_id>[^/]+)/$',
        views.UpdateIPSecSiteConnectionView.as_view(),
        name='update_ipsecsiteconnection'),
    url(r'^addvpnservice$',
        views.AddVPNServiceView.as_view(), name='addvpnservice'),
    url(r'^update_vpnservice/(?P<vpnservice_id>[^/]+)/$',
        views.UpdateVPNServiceView.as_view(), name='update_vpnservice'),
    url(r'^ikepolicy/(?P<ikepolicy_id>[^/]+)/$',
        views.IKEPolicyDetailsView.as_view(), name='ikepolicydetails'),
    url(r'^ipsecpolicy/(?P<ipsecpolicy_id>[^/]+)/$',
        views.IPSecPolicyDetailsView.as_view(), name='ipsecpolicydetails'),
    url(r'^vpnservice/(?P<vpnservice_id>[^/]+)/$',
        views.VPNServiceDetailsView.as_view(), name='vpnservicedetails'),
    url(r'^ipsecsiteconnection/(?P<ipsecsiteconnection_id>[^/]+)/$',
        views.IPSecSiteConnectionDetailsView.as_view(),
        name='ipsecsiteconnectiondetails'))
