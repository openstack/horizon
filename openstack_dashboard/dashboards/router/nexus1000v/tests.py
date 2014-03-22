# vim: tabstop=4 shiftwidth=4 softtabstop=4

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
# @author: Abishek Subramanian, Cisco Systems, Inc.

from django.core.urlresolvers import reverse
from django import http

from mox import IsA  # noqa

from openstack_dashboard import api
from openstack_dashboard.test import helpers as test


def form_data_no_overlay():
    return {'multicast_ip_range': '',
            'sub_type': ''}


def form_data_overlay():
    return {'physical_network': ''}


# TODO(absubram): Remove if clause and create separate
# test stubs for when profile_support is being used and when not.
# Additionally ensure those are always run even in default setting
if api.neutron.is_port_profiles_supported():
    class Nexus1000vTest(test.BaseAdminViewTests):
        @test.create_stubs({api.neutron: ('profile_list',
                                          'profile_bindings_list'),
                            api.keystone: ('tenant_list',)})
        def test_index(self):
            tenants = self.tenants.list()
            net_profiles = self.net_profiles.list()
            policy_profiles = self.policy_profiles.list()
            net_profile_binding = self.network_profile_binding.list()
            policy_profile_binding = self.policy_profile_binding.list()
            api.neutron.profile_list(IsA(http.HttpRequest),
                                     'network').AndReturn(net_profiles)
            api.neutron.profile_list(IsA(http.HttpRequest),
                                     'policy').AndReturn(policy_profiles)
            api.neutron.profile_bindings_list(
                IsA(http.HttpRequest),
                'network').AndReturn(net_profile_binding)
            api.neutron.profile_bindings_list(
                IsA(http.HttpRequest),
                'policy').AndReturn(policy_profile_binding)
            api.keystone.tenant_list(
                IsA(http.HttpRequest)).AndReturn([tenants, False])
            api.keystone.tenant_list(
                IsA(http.HttpRequest)).AndReturn([tenants, False])
            self.mox.ReplayAll()

            res = self.client.get(reverse('horizon:router:nexus1000v:index'))
            self.assertTemplateUsed(res, 'router/nexus1000v/index.html')

        @test.create_stubs({api.neutron: ('profile_create',),
                            api.keystone: ('tenant_list',)})
        def test_create_vlan_net_profile(self):
            tenants = self.tenants.list()
            net_profile = self.net_profiles.first()
            params = {'name': net_profile.name,
                      'segment_type': net_profile.segment_type,
                      'segment_range': net_profile.segment_range,
                      'physical_network': net_profile.physical_network,
                      'tenant_id': net_profile.project,
                      # vlan profiles have no sub_type or multicast_ip_range
                      'multicast_ip_range': '',
                      'sub_type': ''}

            api.neutron.profile_create(IsA(http.HttpRequest),
                                     **params).AndReturn(net_profile)
            api.keystone.tenant_list(
                IsA(http.HttpRequest)).AndReturn([tenants, False])
            self.mox.ReplayAll()

            form_data = {'name': net_profile.name,
                         'segment_type': net_profile.segment_type,
                         'segment_range': net_profile.segment_range,
                         'physical_network': net_profile.physical_network,
                         'project': net_profile.project}
            form_data.update(form_data_no_overlay())
            url = reverse('horizon:router:nexus1000v:create_network_profile')
            res = self.client.post(url, form_data)

            self.assertNoFormErrors(res)
            self.assertRedirectsNoFollow(res,
                                         reverse
                                         ('horizon:router:nexus1000v:index'))

        @test.create_stubs({api.neutron: ('profile_create',),
                            api.keystone: ('tenant_list',)})
        def test_create_overlay_net_profile(self):
            tenants = self.tenants.list()
            net_profile = self.net_profiles.list()[1]
            params = {'name': net_profile.name,
                      'segment_type': net_profile.segment_type,
                      'segment_range': net_profile.segment_range,
                      'multicast_ip_range': net_profile.multicast_ip_range,
                      'sub_type': net_profile.sub_type,
                      'tenant_id': net_profile.project,
                      # overlay profiles have no physical_network type
                      'physical_network': ''}

            api.neutron.profile_create(IsA(http.HttpRequest),
                                     **params).AndReturn(net_profile)
            api.keystone.tenant_list(
                IsA(http.HttpRequest)).AndReturn([tenants, False])
            self.mox.ReplayAll()

            form_data = {'name': net_profile.name,
                         'segment_type': net_profile.segment_type,
                         'segment_range': net_profile.segment_range,
                         'multicast_ip_range': net_profile.multicast_ip_range,
                         'sub_type': net_profile.sub_type,
                         'project': net_profile.project}
            form_data.update(form_data_overlay())
            url = reverse('horizon:router:nexus1000v:create_network_profile')
            res = self.client.post(url, form_data)

            self.assertNoFormErrors(res)
            self.assertRedirectsNoFollow(res,
                                         reverse
                                         ('horizon:router:nexus1000v:index'))

        @test.create_stubs({api.neutron: ('profile_create',),
                            api.keystone: ('tenant_list',)})
        def test_create_overlay_other_net_profile(self):
            tenants = self.tenants.list()
            net_profile = self.net_profiles.list()[2]
            params = {'name': net_profile.name,
                      'segment_type': net_profile.segment_type,
                      'segment_range': net_profile.segment_range,
                      'sub_type': net_profile.other_subtype,
                      'tenant_id': net_profile.project,
                      # overlay 'other' profiles have no multicast_ip_range
                      # or physical_network type
                      'multicast_ip_range': '',
                      'physical_network': ''}

            api.neutron.profile_create(IsA(http.HttpRequest),
                                     **params).AndReturn(net_profile)
            api.keystone.tenant_list(
                IsA(http.HttpRequest)).AndReturn([tenants, False])
            self.mox.ReplayAll()

            form_data = {'name': net_profile.name,
                         'segment_type': net_profile.segment_type,
                         'segment_range': net_profile.segment_range,
                         'sub_type': net_profile.sub_type,
                         'other_subtype': net_profile.other_subtype,
                         'project': net_profile.project}
            form_data.update(form_data_overlay())
            url = reverse('horizon:router:nexus1000v:create_network_profile')
            res = self.client.post(url, form_data)

            self.assertNoFormErrors(res)
            self.assertRedirectsNoFollow(res,
                                         reverse
                                         ('horizon:router:nexus1000v:index'))

        @test.create_stubs({api.neutron: ('profile_create',),
                            api.keystone: ('tenant_list',)})
        def test_create_trunk_net_profile(self):
            tenants = self.tenants.list()
            net_profile = self.net_profiles.list()[3]
            params = {'name': net_profile.name,
                      'segment_type': net_profile.segment_type,
                      'sub_type': net_profile.sub_type_trunk,
                      'tenant_id': net_profile.project,
                      # trunk profiles have no multicast_ip_range,
                      # no segment_range or no physical_network type
                      'multicast_ip_range': '',
                      'segment_range': '',
                      'physical_network': ''}

            api.neutron.profile_create(IsA(http.HttpRequest),
                                     **params).AndReturn(net_profile)
            api.keystone.tenant_list(
                IsA(http.HttpRequest)).AndReturn([tenants, False])
            self.mox.ReplayAll()

            form_data = {'name': net_profile.name,
                         'segment_type': net_profile.segment_type,
                         'sub_type_trunk': net_profile.sub_type_trunk,
                         'project': net_profile.project}
            form_data.update(form_data_no_overlay())
            url = reverse('horizon:router:nexus1000v:create_network_profile')
            res = self.client.post(url, form_data)

            self.assertNoFormErrors(res)
            self.assertRedirectsNoFollow(res,
                                         reverse
                                         ('horizon:router:nexus1000v:index'))
