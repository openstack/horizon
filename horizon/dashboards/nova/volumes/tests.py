# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright 2012 United States Government as represented by the
# Administrator of the National Aeronautics and Space Administration.
# All Rights Reserved.
#
# Copyright 2012 Nebula, Inc.
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

from django import http
from django.conf import settings
from django.core.urlresolvers import reverse
from django.forms import widgets
from mox import IsA

from horizon import api
from horizon import test


class VolumeViewTests(test.TestCase):
    @test.create_stubs({api: ('tenant_quota_usages', 'volume_create',
                              'volume_snapshot_list')})
    def test_create_volume(self):
        volume = self.volumes.first()
        usage = {'gigabytes': {'available': 250}, 'volumes': {'available': 6}}
        formData = {'name': u'A Volume I Am Making',
                    'description': u'This is a volume I am making for a test.',
                    'method': u'CreateForm',
                    'size': 50, 'snapshot_source': ''}

        api.tenant_quota_usages(IsA(http.HttpRequest)).AndReturn(usage)
        api.volume_snapshot_list(IsA(http.HttpRequest)).\
                                 AndReturn(self.volume_snapshots.list())
        api.volume_create(IsA(http.HttpRequest),
                          formData['size'],
                          formData['name'],
                          formData['description'],
                          snapshot_id=None).AndReturn(volume)

        self.mox.ReplayAll()

        url = reverse('horizon:nova:volumes:create')
        res = self.client.post(url, formData)

        redirect_url = reverse('horizon:nova:volumes:index')
        self.assertRedirectsNoFollow(res, redirect_url)

    @test.create_stubs({api: ('tenant_quota_usages', 'volume_create',
                              'volume_snapshot_list'),
                        api.nova: ('volume_snapshot_get',)})
    def test_create_volume_from_snapshot(self):
        volume = self.volumes.first()
        usage = {'gigabytes': {'available': 250}, 'volumes': {'available': 6}}
        snapshot = self.volume_snapshots.first()
        formData = {'name': u'A Volume I Am Making',
                    'description': u'This is a volume I am making for a test.',
                    'method': u'CreateForm',
                    'size': 50, 'snapshot_source': snapshot.id}

        # first call- with url param
        api.tenant_quota_usages(IsA(http.HttpRequest)).AndReturn(usage)
        api.nova.volume_snapshot_get(IsA(http.HttpRequest),
                        str(snapshot.id)).AndReturn(snapshot)
        api.volume_create(IsA(http.HttpRequest),
                          formData['size'],
                          formData['name'],
                          formData['description'],
                          snapshot_id=snapshot.id).\
                          AndReturn(volume)
        # second call- with dropdown
        api.tenant_quota_usages(IsA(http.HttpRequest)).AndReturn(usage)
        api.volume_snapshot_list(IsA(http.HttpRequest)).\
                                 AndReturn(self.volume_snapshots.list())
        api.nova.volume_snapshot_get(IsA(http.HttpRequest),
                        str(snapshot.id)).AndReturn(snapshot)
        api.volume_create(IsA(http.HttpRequest),
                          formData['size'],
                          formData['name'],
                          formData['description'],
                          snapshot_id=snapshot.id).\
                          AndReturn(volume)

        self.mox.ReplayAll()

        # get snapshot from url
        url = reverse('horizon:nova:volumes:create')
        res = self.client.post("?".join([url,
                                         "snapshot_id=" + str(snapshot.id)]),
                               formData)

        redirect_url = reverse('horizon:nova:volumes:index')
        self.assertRedirectsNoFollow(res, redirect_url)

        # get snapshot from dropdown list
        url = reverse('horizon:nova:volumes:create')
        res = self.client.post(url, formData)

        redirect_url = reverse('horizon:nova:volumes:index')
        self.assertRedirectsNoFollow(res, redirect_url)

    @test.create_stubs({api: ('tenant_quota_usages',),
                        api.nova: ('volume_snapshot_get',)})
    def test_create_volume_from_snapshot_invalid_size(self):
        usage = {'gigabytes': {'available': 250}, 'volumes': {'available': 6}}
        snapshot = self.volume_snapshots.first()
        formData = {'name': u'A Volume I Am Making',
                    'description': u'This is a volume I am making for a test.',
                    'method': u'CreateForm',
                    'size': 20, 'snapshot_source': snapshot.id}

        api.tenant_quota_usages(IsA(http.HttpRequest)).AndReturn(usage)
        api.nova.volume_snapshot_get(IsA(http.HttpRequest),
                        str(snapshot.id)).AndReturn(snapshot)
        api.tenant_quota_usages(IsA(http.HttpRequest)).AndReturn(usage)

        self.mox.ReplayAll()

        url = reverse('horizon:nova:volumes:create')
        res = self.client.post("?".join([url,
                                         "snapshot_id=" + str(snapshot.id)]),
                               formData, follow=True)
        self.assertEqual(res.redirect_chain, [])
        self.assertFormError(res, 'form', None,
                             "The volume size cannot be less than the "
                             "snapshot size (40GB)")

    @test.create_stubs({api: ('tenant_quota_usages', 'volume_snapshot_list')})
    def test_create_volume_gb_used_over_alloted_quota(self):
        usage = {'gigabytes': {'available': 100, 'used': 20}}
        formData = {'name': u'This Volume Is Huge!',
                    'description': u'This is a volume that is just too big!',
                    'method': u'CreateForm',
                    'size': 5000}

        api.tenant_quota_usages(IsA(http.HttpRequest)).AndReturn(usage)
        api.volume_snapshot_list(IsA(http.HttpRequest)).\
                                 AndReturn(self.volume_snapshots.list())
        api.tenant_quota_usages(IsA(http.HttpRequest)).AndReturn(usage)

        self.mox.ReplayAll()

        url = reverse('horizon:nova:volumes:create')
        res = self.client.post(url, formData)

        expected_error = [u'A volume of 5000GB cannot be created as you only'
                          ' have 100GB of your quota available.']
        self.assertEqual(res.context['form'].errors['__all__'], expected_error)

    @test.create_stubs({api: ('tenant_quota_usages', 'volume_snapshot_list')})
    def test_create_volume_number_over_alloted_quota(self):
        usage = {'gigabytes': {'available': 100, 'used': 20},
                 'volumes': {'available': 0}}
        formData = {'name': u'Too Many...',
                    'description': u'We have no volumes left!',
                    'method': u'CreateForm',
                    'size': 10}

        api.tenant_quota_usages(IsA(http.HttpRequest)).AndReturn(usage)
        api.volume_snapshot_list(IsA(http.HttpRequest)).\
                                 AndReturn(self.volume_snapshots.list())
        api.tenant_quota_usages(IsA(http.HttpRequest)).AndReturn(usage)

        self.mox.ReplayAll()

        url = reverse('horizon:nova:volumes:create')
        res = self.client.post(url, formData)

        expected_error = [u'You are already using all of your available'
                          ' volumes.']
        self.assertEqual(res.context['form'].errors['__all__'], expected_error)

    @test.create_stubs({api: ('volume_list',
                              'volume_delete',
                              'server_list')})
    def test_delete_volume(self):
        volume = self.volumes.first()
        formData = {'action':
                    'volumes__delete__%s' % volume.id}

        api.volume_list(IsA(http.HttpRequest), search_opts=None).\
                                 AndReturn(self.volumes.list())
        api.volume_delete(IsA(http.HttpRequest), volume.id)
        api.server_list(IsA(http.HttpRequest)).AndReturn(self.servers.list())
        api.volume_list(IsA(http.HttpRequest), search_opts=None).\
                                 AndReturn(self.volumes.list())
        api.server_list(IsA(http.HttpRequest)).AndReturn(self.servers.list())

        self.mox.ReplayAll()

        url = reverse('horizon:nova:volumes:index')
        res = self.client.post(url, formData, follow=True)
        self.assertMessageCount(res, count=0)

    @test.create_stubs({api: ('volume_list',
                              'volume_delete',
                              'server_list')})
    def test_delete_volume_error_existing_snapshot(self):
        volume = self.volumes.first()
        formData = {'action':
                    'volumes__delete__%s' % volume.id}
        exc = self.exceptions.cinder.__class__(400,
                                               "error: dependent snapshots")

        api.volume_list(IsA(http.HttpRequest), search_opts=None).\
                                 AndReturn(self.volumes.list())
        api.volume_delete(IsA(http.HttpRequest), volume.id). \
                          AndRaise(exc)
        api.server_list(IsA(http.HttpRequest)).AndReturn(self.servers.list())
        api.volume_list(IsA(http.HttpRequest), search_opts=None).\
                                 AndReturn(self.volumes.list())
        api.server_list(IsA(http.HttpRequest)).AndReturn(self.servers.list())

        self.mox.ReplayAll()

        url = reverse('horizon:nova:volumes:index')
        res = self.client.post(url, formData, follow=True)
        self.assertMessageCount(res, error=1)
        self.assertEqual(list(res.context['messages'])[0].message,
                         u'Unable to delete volume "%s". '
                         u'One or more snapshots depend on it.' %
                         volume.display_name)

    @test.create_stubs({api: ('volume_get',), api.nova: ('server_list',)})
    def test_edit_attachments(self):
        volume = self.volumes.first()
        servers = self.servers.list()

        api.volume_get(IsA(http.HttpRequest), volume.id).AndReturn(volume)
        api.nova.server_list(IsA(http.HttpRequest)).AndReturn(servers)
        self.mox.ReplayAll()

        url = reverse('horizon:nova:volumes:attach', args=[volume.id])
        res = self.client.get(url)
        # Asserting length of 2 accounts for the one instance option,
        # and the one 'Choose Instance' option.
        form = res.context['form']
        self.assertEqual(len(form.fields['instance']._choices),
                         2)
        self.assertEqual(res.status_code, 200)
        self.assertTrue(isinstance(form.fields['device'].widget,
                                   widgets.TextInput))

    @test.create_stubs({api: ('volume_get',), api.nova: ('server_list',)})
    def test_edit_attachments_cannot_set_mount_point(self):
        PREV = settings.OPENSTACK_HYPERVISOR_FEATURES['can_set_mount_point']
        settings.OPENSTACK_HYPERVISOR_FEATURES['can_set_mount_point'] = False

        volume = self.volumes.first()
        servers = self.servers.list()

        api.volume_get(IsA(http.HttpRequest), volume.id).AndReturn(volume)
        api.nova.server_list(IsA(http.HttpRequest)).AndReturn(servers)
        self.mox.ReplayAll()

        url = reverse('horizon:nova:volumes:attach', args=[volume.id])
        res = self.client.get(url)
        # Assert the device field is hidden.
        form = res.context['form']
        self.assertTrue(isinstance(form.fields['device'].widget,
                                   widgets.HiddenInput))
        settings.OPENSTACK_HYPERVISOR_FEATURES['can_set_mount_point'] = PREV

    @test.create_stubs({api: ('volume_get',),
                        api.nova: ('server_get', 'server_list',)})
    def test_edit_attachments_attached_volume(self):
        server = self.servers.first()
        volume = self.volumes.list()[0]

        api.volume_get(IsA(http.HttpRequest), volume.id) \
                       .AndReturn(volume)
        api.nova.server_list(IsA(http.HttpRequest)) \
                             .AndReturn(self.servers.list())

        self.mox.ReplayAll()

        url = reverse('horizon:nova:volumes:attach',
                      args=[volume.id])
        res = self.client.get(url)

        self.assertEqual(res.context['form'].fields['instance']._choices[0][1],
                         "Select an instance")
        self.assertEqual(len(res.context['form'].fields['instance'].choices),
                         2)
        self.assertEqual(res.context['form'].fields['instance']._choices[1][0],
                         server.id)
        self.assertEqual(res.status_code, 200)

    @test.create_stubs({api.nova: ('volume_get', 'server_get',)})
    def test_detail_view(self):
        volume = self.volumes.first()
        server = self.servers.first()

        volume.attachments = [{"server_id": server.id}]

        api.nova.volume_get(IsA(http.HttpRequest), volume.id).AndReturn(volume)
        api.nova.server_get(IsA(http.HttpRequest), server.id).AndReturn(server)

        self.mox.ReplayAll()

        url = reverse('horizon:nova:volumes:detail',
                      args=[volume.id])
        res = self.client.get(url)

        self.assertContains(res, "<dd>Volume name</dd>", 1, 200)
        self.assertContains(res,
                            "<dd>41023e92-8008-4c8b-8059-7f2293ff3775</dd>",
                            1,
                            200)
        self.assertContains(res, "<dd>Available</dd>", 1, 200)
        self.assertContains(res, "<dd>40 GB</dd>", 1, 200)
        self.assertContains(res,
                            ("<a href=\"/nova/instances/1/\">%s</a>"
                             % server.name),
                            1,
                            200)

        self.assertNoMessages()
