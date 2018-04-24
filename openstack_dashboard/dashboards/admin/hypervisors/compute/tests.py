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

from django.urls import reverse

from openstack_dashboard import api
from openstack_dashboard.test import helpers as test


class EvacuateHostViewTest(test.BaseAdminViewTests):
    @test.create_mocks({api.nova: ['service_list']})
    def test_index(self):
        hypervisor = self.hypervisors.list().pop().hypervisor_hostname
        services = [service for service in self.services.list()
                    if service.binary == 'nova-compute']
        self.mock_service_list.return_value = services

        url = reverse('horizon:admin:hypervisors:compute:evacuate_host',
                      args=[hypervisor])
        res = self.client.get(url)
        self.assertTemplateUsed(res,
                                'admin/hypervisors/compute/evacuate_host.html')

        self.mock_service_list.assert_called_once_with(
            test.IsHttpRequest(), binary='nova-compute')

    @test.create_mocks({api.nova: ['service_list',
                                   'evacuate_host']})
    def test_successful_post(self):
        hypervisor = self.hypervisors.list().pop().hypervisor_hostname
        services = [service for service in self.services.list()
                    if service.binary == 'nova-compute']

        self.mock_service_list.return_value = services
        self.mock_evacuate_host.return_value = True

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

        self.mock_service_list.assert_called_once_with(
            test.IsHttpRequest(), binary='nova-compute')
        self.mock_evacuate_host.assert_called_once_with(
            test.IsHttpRequest(),
            services[1].host,
            services[0].host,
            False)

    @test.create_mocks({api.nova: ['service_list',
                                   'evacuate_host']})
    def test_failing_nova_call_post(self):
        hypervisor = self.hypervisors.list().pop().hypervisor_hostname
        services = [service for service in self.services.list()
                    if service.binary == 'nova-compute']

        self.mock_service_list.return_value = services
        self.mock_evacuate_host.side_effect = self.exceptions.nova

        url = reverse('horizon:admin:hypervisors:compute:evacuate_host',
                      args=[hypervisor])

        form_data = {'current_host': services[1].host,
                     'target_host': services[0].host,
                     'on_shared_storage': False}

        res = self.client.post(url, form_data)
        dest_url = reverse('horizon:admin:hypervisors:index')
        self.assertMessageCount(error=1)
        self.assertRedirectsNoFollow(res, dest_url)

        self.mock_service_list.assert_called_once_with(
            test.IsHttpRequest(), binary='nova-compute')
        self.mock_evacuate_host.assert_called_once_with(
            test.IsHttpRequest(),
            services[1].host,
            services[0].host,
            False)


class MigrateHostViewTest(test.BaseAdminViewTests):
    def test_index(self):
        disabled_services = [service for service in self.services.list()
                             if (service.binary == 'nova-compute' and
                                 service.status == 'disabled')]
        disabled_service = disabled_services[0]

        url = reverse('horizon:admin:hypervisors:compute:migrate_host',
                      args=[disabled_service.host])
        res = self.client.get(url)
        self.assertNoMessages()
        self.assertTemplateUsed(res,
                                'admin/hypervisors/compute/migrate_host.html')

    @test.create_mocks({api.nova: ['migrate_host']})
    def test_maintenance_host_cold_migration_succeed(self):
        disabled_services = [service for service in self.services.list()
                             if (service.binary == 'nova-compute' and
                                 service.status == 'disabled')]
        disabled_service = disabled_services[0]
        self.mock_migrate_host.return_value = True

        url = reverse('horizon:admin:hypervisors:compute:migrate_host',
                      args=[disabled_service.host])
        form_data = {'current_host': disabled_service.host,
                     'migrate_type': 'cold_migrate',
                     'disk_over_commit': False,
                     'block_migration': False}
        res = self.client.post(url, form_data)
        dest_url = reverse('horizon:admin:hypervisors:index')
        self.assertNoFormErrors(res)
        self.assertMessageCount(success=1)
        self.assertRedirectsNoFollow(res, dest_url)

        self.mock_migrate_host.assert_called_once_with(
            test.IsHttpRequest(),
            disabled_service.host,
            live_migrate=False,
            disk_over_commit=False,
            block_migration=False)

    @test.create_mocks({api.nova: ['migrate_host']})
    def test_maintenance_host_live_migration_succeed(self):
        disabled_services = [service for service in self.services.list()
                             if (service.binary == 'nova-compute' and
                                 service.status == 'disabled')]
        disabled_service = disabled_services[0]
        self.mock_migrate_host.return_value = True
        url = reverse('horizon:admin:hypervisors:compute:migrate_host',
                      args=[disabled_service.host])
        form_data = {'current_host': disabled_service.host,
                     'migrate_type': 'live_migrate',
                     'disk_over_commit': False,
                     'block_migration': True}
        res = self.client.post(url, form_data)
        dest_url = reverse('horizon:admin:hypervisors:index')
        self.assertNoFormErrors(res)
        self.assertMessageCount(success=1)
        self.assertRedirectsNoFollow(res, dest_url)

        self.mock_migrate_host.assert_called_once_with(
            test.IsHttpRequest(),
            disabled_service.host,
            live_migrate=True,
            disk_over_commit=False,
            block_migration=True)

    @test.create_mocks({api.nova: ['migrate_host']})
    def test_maintenance_host_migration_fails(self):
        disabled_services = [service for service in self.services.list()
                             if (service.binary == 'nova-compute' and
                                 service.status == 'disabled')]
        disabled_service = disabled_services[0]

        self.mock_migrate_host.side_effect = self.exceptions.nova

        url = reverse('horizon:admin:hypervisors:compute:migrate_host',
                      args=[disabled_service.host])
        form_data = {'current_host': disabled_service.host,
                     'migrate_type': 'live_migrate',
                     'disk_over_commit': False,
                     'block_migration': True}
        res = self.client.post(url, form_data)
        dest_url = reverse('horizon:admin:hypervisors:index')
        self.assertMessageCount(error=1)
        self.assertRedirectsNoFollow(res, dest_url)

        self.mock_migrate_host.assert_called_once_with(
            test.IsHttpRequest(),
            disabled_service.host,
            live_migrate=True,
            disk_over_commit=False,
            block_migration=True)


class DisableServiceViewTest(test.BaseAdminViewTests):
    def test_index(self):
        hypervisor = self.hypervisors.list().pop().hypervisor_hostname

        url = reverse('horizon:admin:hypervisors:compute:disable_service',
                      args=[hypervisor])
        res = self.client.get(url)
        template = 'admin/hypervisors/compute/disable_service.html'
        self.assertTemplateUsed(res, template)

    @test.create_mocks({api.nova: ['service_disable']})
    def test_successful_post(self):
        hypervisor = self.hypervisors.list().pop().hypervisor_hostname
        services = [service for service in self.services.list()
                    if service.binary == 'nova-compute']

        self.mock_service_disable.return_value = True

        url = reverse('horizon:admin:hypervisors:compute:disable_service',
                      args=[hypervisor])

        form_data = {'host': services[0].host,
                     'reason': 'test disable'}

        res = self.client.post(url, form_data)
        dest_url = reverse('horizon:admin:hypervisors:index')
        self.assertNoFormErrors(res)
        self.assertMessageCount(success=1)
        self.assertRedirectsNoFollow(res, dest_url)

        self.mock_service_disable.assert_called_once_with(
            test.IsHttpRequest(),
            services[0].host,
            'nova-compute',
            reason='test disable')

    @test.create_mocks({api.nova: ['service_disable']})
    def test_failing_nova_call_post(self):
        hypervisor = self.hypervisors.list().pop().hypervisor_hostname
        services = [service for service in self.services.list()
                    if service.binary == 'nova-compute']

        self.mock_service_disable.side_effect = self.exceptions.nova

        url = reverse('horizon:admin:hypervisors:compute:disable_service',
                      args=[hypervisor])

        form_data = {'host': services[0].host,
                     'reason': 'test disable'}

        res = self.client.post(url, form_data)
        dest_url = reverse('horizon:admin:hypervisors:index')
        self.assertMessageCount(error=1)
        self.assertRedirectsNoFollow(res, dest_url)

        self.mock_service_disable.assert_called_once_with(
            test.IsHttpRequest(),
            services[0].host,
            'nova-compute',
            reason='test disable')
