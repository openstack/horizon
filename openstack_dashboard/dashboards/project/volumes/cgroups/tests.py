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

import django
from django.core.urlresolvers import reverse
from django import http
from django.utils.http import urlunquote
from mox3.mox import IsA  # noqa

from openstack_dashboard.api import cinder
from openstack_dashboard.test import helpers as test


VOLUME_INDEX_URL = reverse('horizon:project:volumes:index')
VOLUME_CGROUPS_TAB_URL = urlunquote(reverse(
    'horizon:project:volumes:cgroups_tab'))


class ConsistencyGroupTests(test.TestCase):
    @test.create_stubs({cinder: ('volume_cgroup_create',
                                 'volume_cgroup_list',
                                 'volume_type_list',
                                 'volume_type_list_with_qos_associations',
                                 'availability_zone_list',
                                 'extension_supported')})
    def test_create_cgroup(self):
        cgroup = self.cinder_consistencygroups.first()
        volume_types = self.cinder_volume_types.list()
        az = self.cinder_availability_zones.first().zoneName
        formData = {'volume_types': '1',
                    'name': 'test CG',
                    'description': 'test desc',
                    'availability_zone': az}

        cinder.volume_type_list(IsA(http.HttpRequest)).\
            AndReturn(volume_types)
        cinder.volume_type_list_with_qos_associations(IsA(http.HttpRequest)).\
            AndReturn(volume_types)
        cinder.availability_zone_list(IsA(http.HttpRequest)).AndReturn(
            self.cinder_availability_zones.list())
        cinder.extension_supported(IsA(http.HttpRequest), 'AvailabilityZones')\
            .AndReturn(True)
        cinder.volume_cgroup_list(IsA(
            http.HttpRequest)).\
            AndReturn(self.cinder_consistencygroups.list())
        cinder.volume_cgroup_create(
            IsA(http.HttpRequest),
            formData['volume_types'],
            formData['name'],
            formData['description'],
            availability_zone=formData['availability_zone'])\
            .AndReturn(cgroup)
        self.mox.ReplayAll()

        url = reverse('horizon:project:volumes:cgroups:create')
        res = self.client.post(url, formData)
        self.assertNoFormErrors(res)

    @test.create_stubs({cinder: ('volume_cgroup_create',
                                 'volume_cgroup_list',
                                 'volume_type_list',
                                 'volume_type_list_with_qos_associations',
                                 'availability_zone_list',
                                 'extension_supported')})
    def test_create_cgroup_exception(self):
        volume_types = self.cinder_volume_types.list()
        az = self.cinder_availability_zones.first().zoneName
        formData = {'volume_types': '1',
                    'name': 'test CG',
                    'description': 'test desc',
                    'availability_zone': az}

        cinder.volume_type_list(IsA(http.HttpRequest)).\
            AndReturn(volume_types)
        cinder.volume_type_list_with_qos_associations(IsA(http.HttpRequest)).\
            AndReturn(volume_types)
        cinder.availability_zone_list(IsA(http.HttpRequest)).AndReturn(
            self.cinder_availability_zones.list())
        cinder.extension_supported(IsA(http.HttpRequest), 'AvailabilityZones')\
            .AndReturn(True)
        cinder.volume_cgroup_list(IsA(
            http.HttpRequest)).\
            AndReturn(self.cinder_consistencygroups.list())
        cinder.volume_cgroup_create(
            IsA(http.HttpRequest),
            formData['volume_types'],
            formData['name'],
            formData['description'],
            availability_zone=formData['availability_zone'])\
            .AndRaise(self.exceptions.cinder)
        self.mox.ReplayAll()

        url = reverse('horizon:project:volumes:cgroups:create')
        res = self.client.post(url, formData)

        self.assertRedirectsNoFollow(res, VOLUME_INDEX_URL)

    @test.create_stubs({cinder: ('volume_cgroup_list_with_vol_type_names',
                                 'volume_cgroup_delete')})
    def test_delete_cgroup(self):
        cgroups = self.cinder_consistencygroups.list()
        cgroup = self.cinder_consistencygroups.first()

        cinder.volume_cgroup_list_with_vol_type_names(IsA(http.HttpRequest)).\
            AndReturn(cgroups)
        cinder.volume_cgroup_delete(IsA(http.HttpRequest), cgroup.id,
                                    force=False)
        if django.VERSION < (1, 9):
            cinder.volume_cgroup_list_with_vol_type_names(
                IsA(http.HttpRequest)).AndReturn(cgroups)

        self.mox.ReplayAll()

        formData = {'action': 'volume_cgroups__deletecg__%s' % cgroup.id}
        res = self.client.post(VOLUME_CGROUPS_TAB_URL, formData, follow=True)
        self.assertIn("Scheduled deletion of Consistency Group: cg_1",
                      [m.message for m in res.context['messages']])

    @test.create_stubs({cinder: ('volume_cgroup_update',
                                 'volume_cgroup_get')})
    def test_update_cgroup_add_vol(self):
        cgroup = self.cinder_consistencygroups.first()
        volume = self.cinder_volumes.first()
        formData = {'volume_types': '1',
                    'name': 'test CG',
                    'description': 'test desc'}

        cinder.volume_cgroup_get(IsA(
            http.HttpRequest), cgroup.id).\
            AndReturn(cgroup)
        cinder.volume_cgroup_update(
            IsA(http.HttpRequest),
            formData['name'],
            formData['description'],
            add_vols=volume)\
            .AndReturn(cgroup)
        self.mox.ReplayAll()

        url = reverse('horizon:project:volumes:cgroups:update',
                      args=[cgroup.id])
        res = self.client.post(url, formData)
        self.assertNoFormErrors(res)

    @test.create_stubs({cinder: ('volume_cgroup_update',
                                 'volume_cgroup_get')})
    def test_update_cgroup_remove_vol(self):
        cgroup = self.cinder_consistencygroups.first()
        volume = self.cinder_volumes.first()
        formData = {'volume_types': '1',
                    'name': 'test CG',
                    'description': 'test desc'}

        cinder.volume_cgroup_get(IsA(
            http.HttpRequest), cgroup.id).\
            AndReturn(cgroup)
        cinder.volume_cgroup_update(
            IsA(http.HttpRequest),
            formData['name'],
            formData['description'],
            remove_vols=volume)\
            .AndReturn(cgroup)
        self.mox.ReplayAll()

        url = reverse('horizon:project:volumes:cgroups:update',
                      args=[cgroup.id])
        res = self.client.post(url, formData)
        self.assertNoFormErrors(res)

    @test.create_stubs({cinder: ('volume_cgroup_update',
                                 'volume_cgroup_get')})
    def test_update_cgroup_name_and_description(self):
        cgroup = self.cinder_consistencygroups.first()
        formData = {'volume_types': '1',
                    'name': 'test CG-new',
                    'description': 'test desc-new'}

        cinder.volume_cgroup_get(IsA(
            http.HttpRequest), cgroup.id).\
            AndReturn(cgroup)
        cinder.volume_cgroup_update(
            IsA(http.HttpRequest),
            formData['name'],
            formData['description'])\
            .AndReturn(cgroup)
        self.mox.ReplayAll()

        url = reverse('horizon:project:volumes:cgroups:update',
                      args=[cgroup.id])
        res = self.client.post(url, formData)
        self.assertNoFormErrors(res)

    @test.create_stubs({cinder: ('volume_cgroup_update',
                                 'volume_cgroup_get')})
    def test_update_cgroup_with_exception(self):
        cgroup = self.cinder_consistencygroups.first()
        formData = {'volume_types': '1',
                    'name': 'test CG-new',
                    'description': 'test desc-new'}

        cinder.volume_cgroup_get(IsA(
            http.HttpRequest), cgroup.id).\
            AndReturn(cgroup)
        cinder.volume_cgroup_update(
            IsA(http.HttpRequest),
            formData['name'],
            formData['description'])\
            .AndRaise(self.exceptions.cinder)
        self.mox.ReplayAll()

        url = reverse('horizon:project:volumes:cgroups:update',
                      args=[cgroup.id])
        res = self.client.post(url, formData)

        self.assertRedirectsNoFollow(res, VOLUME_INDEX_URL)

    @test.create_stubs({cinder: ('volume_cgroup_get',)})
    def test_detail_view_with_exception(self):
        cgroup = self.cinder_consistencygroups.first()

        cinder.volume_cgroup_get(IsA(http.HttpRequest), cgroup.id).\
            AndRaise(self.exceptions.cinder)

        self.mox.ReplayAll()

        url = reverse('horizon:project:volumes:cgroups:detail',
                      args=[cgroup.id])
        res = self.client.get(url)

        self.assertRedirectsNoFollow(res, VOLUME_INDEX_URL)
