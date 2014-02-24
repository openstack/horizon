# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

from django.core.urlresolvers import reverse
from django import http
from mox import IsA  # noqa

from openstack_dashboard import api
from openstack_dashboard.test import helpers as test


class EvacuateHostViewTest(test.BaseAdminViewTests):
    @test.create_stubs({api.nova: ('hypervisor_list',
                                   'hypervisor_stats',
                                   'service_list')})
    def test_index(self):
        hypervisor = self.hypervisors.list().pop().hypervisor_hostname
        services = [service for service in self.services.list()
                    if service.binary == 'nova-compute']
        api.nova.service_list(IsA(http.HttpRequest),
                              binary='nova-compute').AndReturn(services)

        self.mox.ReplayAll()

        url = reverse('horizon:admin:hypervisors:compute:evacuate_host',
                      args=[hypervisor])
        res = self.client.get(url)
        self.assertTemplateUsed(res,
                                'admin/hypervisors/compute/evacuate_host.html')

    @test.create_stubs({api.nova: ('hypervisor_list',
                                   'hypervisor_stats',
                                   'service_list',
                                   'evacuate_host')})
    def test_successful_post(self):
        hypervisor = self.hypervisors.list().pop().hypervisor_hostname
        services = [service for service in self.services.list()
                    if service.binary == 'nova-compute']

        api.nova.service_list(IsA(http.HttpRequest),
                              binary='nova-compute').AndReturn(services)
        api.nova.evacuate_host(IsA(http.HttpRequest),
                               services[1].host,
                               services[0].host,
                               False).AndReturn(True)
        self.mox.ReplayAll()

        url = reverse('horizon:admin:hypervisors:compute:evacuate_host',
                      args=[hypervisor])

        form_data = {'current_host': services[1].host,
                     'target_host': services[0].host,
                     'on_shared_storage': False}

        res = self.client.post(url, form_data)
        dest_url = reverse('horizon:admin:hypervisors:index')
        self.assertNoFormErrors(res)
        self.assertMessageCount(success=1)
        self.assertRedirectsNoFollow(res, dest_url)

    @test.create_stubs({api.nova: ('hypervisor_list',
                                   'hypervisor_stats',
                                   'service_list',
                                   'evacuate_host')})
    def test_failing_nova_call_post(self):
        hypervisor = self.hypervisors.list().pop().hypervisor_hostname
        services = [service for service in self.services.list()
                    if service.binary == 'nova-compute']

        api.nova.service_list(IsA(http.HttpRequest),
                              binary='nova-compute').AndReturn(services)
        api.nova.evacuate_host(IsA(http.HttpRequest),
                               services[1].host,
                               services[0].host,
                               False).AndRaise(self.exceptions.nova)
        self.mox.ReplayAll()

        url = reverse('horizon:admin:hypervisors:compute:evacuate_host',
                      args=[hypervisor])

        form_data = {'current_host': services[1].host,
                     'target_host': services[0].host,
                     'on_shared_storage': False}

        res = self.client.post(url, form_data)
        dest_url = reverse('horizon:admin:hypervisors:index')
        self.assertMessageCount(error=1)
        self.assertRedirectsNoFollow(res, dest_url)