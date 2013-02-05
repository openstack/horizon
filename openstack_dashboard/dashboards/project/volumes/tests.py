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

from openstack_dashboard import api
from openstack_dashboard.api import cinder
from openstack_dashboard.test import helpers as test
from openstack_dashboard.usage import quotas


class VolumeViewTests(test.TestCase):
    @test.create_stubs({cinder: ('volume_create',
                                 'volume_snapshot_list',
                                 'volume_type_list',),
                        quotas: ('tenant_quota_usages',)})
    def test_create_volume(self):
        volume = self.volumes.first()
        volume_type = self.volume_types.first()
        usage = {'gigabytes': {'available': 250}, 'volumes': {'available': 6}}
        formData = {'name': u'A Volume I Am Making',
                    'description': u'This is a volume I am making for a test.',
                    'method': u'CreateForm',
                    'type': volume_type.name,
                    'size': 50,
                    'snapshot_source': ''}

        cinder.volume_type_list(IsA(http.HttpRequest)).\
                                AndReturn(self.volume_types.list())
        quotas.tenant_quota_usages(IsA(http.HttpRequest)).AndReturn(usage)
        cinder.volume_snapshot_list(IsA(http.HttpRequest)).\
                                    AndReturn(self.volume_snapshots.list())
        cinder.volume_create(IsA(http.HttpRequest),
                             formData['size'],
                             formData['name'],
                             formData['description'],
                             formData['type'],
                             metadata={},
                             snapshot_id=None).AndReturn(volume)

        self.mox.ReplayAll()

        url = reverse('horizon:project:volumes:create')
        res = self.client.post(url, formData)

        redirect_url = reverse('horizon:project:volumes:index')
        self.assertRedirectsNoFollow(res, redirect_url)

    @test.create_stubs({cinder: ('volume_create',
                                 'volume_snapshot_list',
                                 'volume_snapshot_get',
                                 'volume_get',
                                 'volume_type_list',),
                        quotas: ('tenant_quota_usages',)})
    def test_create_volume_from_snapshot(self):
        volume = self.volumes.first()
        usage = {'gigabytes': {'available': 250}, 'volumes': {'available': 6}}
        snapshot = self.volume_snapshots.first()
        formData = {'name': u'A Volume I Am Making',
                    'description': u'This is a volume I am making for a test.',
                    'method': u'CreateForm',
                    'size': 50,
                    'type': '',
                    'snapshot_source': snapshot.id}

        # first call- with url param
        cinder.volume_type_list(IsA(http.HttpRequest)).\
                                AndReturn(self.volume_types.list())
        quotas.tenant_quota_usages(IsA(http.HttpRequest)).AndReturn(usage)
        cinder.volume_snapshot_get(IsA(http.HttpRequest),
                                   str(snapshot.id)).AndReturn(snapshot)
        cinder.volume_get(IsA(http.HttpRequest), snapshot.volume_id).\
                          AndReturn(self.volumes.first())
        cinder.volume_create(IsA(http.HttpRequest),
                             formData['size'],
                             formData['name'],
                             formData['description'],
                             '',
                             metadata={},
                             snapshot_id=snapshot.id).\
                             AndReturn(volume)
        # second call- with dropdown
        cinder.volume_type_list(IsA(http.HttpRequest)).\
                                AndReturn(self.volume_types.list())
        quotas.tenant_quota_usages(IsA(http.HttpRequest)).AndReturn(usage)
        cinder.volume_snapshot_list(IsA(http.HttpRequest)).\
                                 AndReturn(self.volume_snapshots.list())
        cinder.volume_snapshot_get(IsA(http.HttpRequest),
                                   str(snapshot.id)).AndReturn(snapshot)
        cinder.volume_create(IsA(http.HttpRequest),
                             formData['size'],
                             formData['name'],
                             formData['description'],
                             '',
                             metadata={},
                             snapshot_id=snapshot.id).\
                             AndReturn(volume)

        self.mox.ReplayAll()

        # get snapshot from url
        url = reverse('horizon:project:volumes:create')
        res = self.client.post("?".join([url,
                                         "snapshot_id=" + str(snapshot.id)]),
                               formData)

        redirect_url = reverse('horizon:project:volumes:index')
        self.assertRedirectsNoFollow(res, redirect_url)

        # get snapshot from dropdown list
        url = reverse('horizon:project:volumes:create')
        res = self.client.post(url, formData)

        redirect_url = reverse('horizon:project:volumes:index')
        self.assertRedirectsNoFollow(res, redirect_url)

    @test.create_stubs({cinder: ('volume_snapshot_get',
                                 'volume_type_list',
                                 'volume_get',),
                        quotas: ('tenant_quota_usages',)})
    def test_create_volume_from_snapshot_invalid_size(self):
        usage = {'gigabytes': {'available': 250}, 'volumes': {'available': 6}}
        snapshot = self.volume_snapshots.first()
        formData = {'name': u'A Volume I Am Making',
                    'description': u'This is a volume I am making for a test.',
                    'method': u'CreateForm',
                    'size': 20, 'snapshot_source': snapshot.id}

        cinder.volume_type_list(IsA(http.HttpRequest)).\
                                AndReturn(self.volume_types.list())
        quotas.tenant_quota_usages(IsA(http.HttpRequest)).AndReturn(usage)
        cinder.volume_snapshot_get(IsA(http.HttpRequest),
                                   str(snapshot.id)).AndReturn(snapshot)
        cinder.volume_get(IsA(http.HttpRequest), snapshot.volume_id).\
                          AndReturn(self.volumes.first())
        quotas.tenant_quota_usages(IsA(http.HttpRequest)).AndReturn(usage)

        self.mox.ReplayAll()

        url = reverse('horizon:project:volumes:create')
        res = self.client.post("?".join([url,
                                         "snapshot_id=" + str(snapshot.id)]),
                               formData, follow=True)
        self.assertEqual(res.redirect_chain, [])
        self.assertFormError(res, 'form', None,
                             "The volume size cannot be less than the "
                             "snapshot size (40GB)")

    @test.create_stubs({cinder: ('volume_snapshot_list', 'volume_type_list',),
                        quotas: ('tenant_quota_usages',)})
    def test_create_volume_gb_used_over_alloted_quota(self):
        usage = {'gigabytes': {'available': 100, 'used': 20}}
        formData = {'name': u'This Volume Is Huge!',
                    'description': u'This is a volume that is just too big!',
                    'method': u'CreateForm',
                    'size': 5000}

        cinder.volume_type_list(IsA(http.HttpRequest)).\
                                AndReturn(self.volume_types.list())
        quotas.tenant_quota_usages(IsA(http.HttpRequest)).AndReturn(usage)
        cinder.volume_snapshot_list(IsA(http.HttpRequest)).\
                                    AndReturn(self.volume_snapshots.list())
        quotas.tenant_quota_usages(IsA(http.HttpRequest)).AndReturn(usage)

        self.mox.ReplayAll()

        url = reverse('horizon:project:volumes:create')
        res = self.client.post(url, formData)

        expected_error = [u'A volume of 5000GB cannot be created as you only'
                          ' have 100GB of your quota available.']
        self.assertEqual(res.context['form'].errors['__all__'], expected_error)

    @test.create_stubs({cinder: ('volume_snapshot_list', 'volume_type_list',),
                        quotas: ('tenant_quota_usages',)})
    def test_create_volume_number_over_alloted_quota(self):
        usage = {'gigabytes': {'available': 100, 'used': 20},
                 'volumes': {'available': 0}}
        formData = {'name': u'Too Many...',
                    'description': u'We have no volumes left!',
                    'method': u'CreateForm',
                    'size': 10}

        cinder.volume_type_list(IsA(http.HttpRequest)).\
                                AndReturn(self.volume_types.list())
        quotas.tenant_quota_usages(IsA(http.HttpRequest)).AndReturn(usage)
        cinder.volume_snapshot_list(IsA(http.HttpRequest)).\
                                    AndReturn(self.volume_snapshots.list())
        quotas.tenant_quota_usages(IsA(http.HttpRequest)).AndReturn(usage)

        self.mox.ReplayAll()

        url = reverse('horizon:project:volumes:create')
        res = self.client.post(url, formData)

        expected_error = [u'You are already using all of your available'
                          ' volumes.']
        self.assertEqual(res.context['form'].errors['__all__'], expected_error)

    @test.create_stubs({cinder: ('volume_create',
                                 'volume_snapshot_list',
                                 'volume_type_list',),
                        quotas: ('tenant_quota_usages',)})
    def test_create_volume_encrypted(self):
        volume = self.volumes.first()
        volume_type = self.volume_types.first()
        usage = {'gigabytes': {'available': 250}, 'volumes': {'available': 6}}
        formData = {'name': u'An Encrypted Volume',
                    'description': u'This volume has metadata for encryption.',
                    'method': u'CreateForm',
                    'type': volume_type.name,
                    'size': 50,
                    'snapshot_source': '',
                    'encryption': u'LUKS'}

        # check normal operation with can_encrypt_volumes = true
        PREV = settings.OPENSTACK_HYPERVISOR_FEATURES['can_encrypt_volumes']
        settings.OPENSTACK_HYPERVISOR_FEATURES['can_encrypt_volumes'] = True

        cinder.volume_type_list(IsA(http.HttpRequest)).\
                                AndReturn(self.volume_types.list())
        quotas.tenant_quota_usages(IsA(http.HttpRequest)).AndReturn(usage)
        cinder.volume_snapshot_list(IsA(http.HttpRequest)).\
                                    AndReturn(self.volume_snapshots.list())
        cinder.volume_create(IsA(http.HttpRequest),
                             formData['size'],
                             formData['name'],
                             formData['description'],
                             formData['type'],
                             metadata={'encryption': formData['encryption']},
                             snapshot_id=None).AndReturn(volume)

        self.mox.ReplayAll()

        url = reverse('horizon:project:volumes:create')
        res = self.client.post(url, formData)

        redirect_url = reverse('horizon:project:volumes:index')
        self.assertRedirectsNoFollow(res, redirect_url)

        settings.OPENSTACK_HYPERVISOR_FEATURES['can_encrypt_volumes'] = PREV

    @test.create_stubs({cinder: ('volume_snapshot_list', 'volume_type_list',),
                        quotas: ('tenant_quota_usages',)})
    def test_create_volume_cannot_encrypt(self):
        volume = self.volumes.first()
        volume_type = self.volume_types.first()
        usage = {'gigabytes': {'available': 250}, 'volumes': {'available': 6}}
        formData = {'name': u'An Encrypted Volume',
                    'description': u'This volume has metadata for encryption.',
                    'method': u'CreateForm',
                    'type': volume_type.name,
                    'size': 50,
                    'snapshot_source': '',
                    'encryption': u'LUKS'}

        # check that widget is hidden if can_encrypt_volumes = false
        PREV = settings.OPENSTACK_HYPERVISOR_FEATURES['can_encrypt_volumes']
        settings.OPENSTACK_HYPERVISOR_FEATURES['can_encrypt_volumes'] = False

        volume = self.volumes.first()
        volume_type = self.volume_types.first()
        usage = {'gigabytes': {'available': 250}, 'volumes': {'available': 6}}

        cinder.volume_type_list(IsA(http.HttpRequest)).\
                                AndReturn(self.volume_types.list())
        quotas.tenant_quota_usages(IsA(http.HttpRequest)).AndReturn(usage)
        cinder.volume_snapshot_list(IsA(http.HttpRequest)).\
                                    AndReturn(self.volume_snapshots.list())

        self.mox.ReplayAll()

        url = reverse('horizon:project:volumes:create')
        res = self.client.get(url)

        # Assert the encryption field is hidden.
        form = res.context['form']
        self.assertTrue(isinstance(form.fields['encryption'].widget,
                                   widgets.HiddenInput))

        settings.OPENSTACK_HYPERVISOR_FEATURES['can_encrypt_volumes'] = PREV

    @test.create_stubs({cinder: ('volume_list',
                                 'volume_delete',),
                        api.nova: ('server_list',)})
    def test_delete_volume(self):
        volume = self.volumes.first()
        formData = {'action':
                    'volumes__delete__%s' % volume.id}

        cinder.volume_list(IsA(http.HttpRequest), search_opts=None).\
                           AndReturn(self.volumes.list())
        cinder.volume_delete(IsA(http.HttpRequest), volume.id)
        api.nova.server_list(IsA(http.HttpRequest)).\
                             AndReturn(self.servers.list())
        cinder.volume_list(IsA(http.HttpRequest), search_opts=None).\
                           AndReturn(self.volumes.list())
        api.nova.server_list(IsA(http.HttpRequest)).\
                             AndReturn(self.servers.list())

        self.mox.ReplayAll()

        url = reverse('horizon:project:volumes:index')
        res = self.client.post(url, formData, follow=True)
        self.assertIn("Scheduled deletion of Volume: Volume name",
                      [m.message for m in res.context['messages']])

    @test.create_stubs({cinder: ('volume_list',
                                 'volume_delete',),
                        api.nova: ('server_list',)})
    def test_delete_volume_error_existing_snapshot(self):
        volume = self.volumes.first()
        formData = {'action':
                    'volumes__delete__%s' % volume.id}
        exc = self.exceptions.cinder.__class__(400,
                                               "error: dependent snapshots")

        cinder.volume_list(IsA(http.HttpRequest), search_opts=None).\
                           AndReturn(self.volumes.list())
        cinder.volume_delete(IsA(http.HttpRequest), volume.id).\
                             AndRaise(exc)
        api.nova.server_list(IsA(http.HttpRequest)).\
                             AndReturn(self.servers.list())
        cinder.volume_list(IsA(http.HttpRequest), search_opts=None).\
                           AndReturn(self.volumes.list())
        api.nova.server_list(IsA(http.HttpRequest)).\
                             AndReturn(self.servers.list())

        self.mox.ReplayAll()

        url = reverse('horizon:project:volumes:index')
        res = self.client.post(url, formData, follow=True)
        self.assertMessageCount(res, error=1)
        self.assertEqual(list(res.context['messages'])[0].message,
                         u'Unable to delete volume "%s". '
                         u'One or more snapshots depend on it.' %
                         volume.display_name)

    @test.create_stubs({cinder: ('volume_get',), api.nova: ('server_list',)})
    def test_edit_attachments(self):
        volume = self.volumes.first()
        servers = self.servers.list()

        cinder.volume_get(IsA(http.HttpRequest), volume.id).AndReturn(volume)
        api.nova.server_list(IsA(http.HttpRequest)).AndReturn(servers)
        self.mox.ReplayAll()

        url = reverse('horizon:project:volumes:attach', args=[volume.id])
        res = self.client.get(url)
        # Asserting length of 2 accounts for the one instance option,
        # and the one 'Choose Instance' option.
        form = res.context['form']
        self.assertEqual(len(form.fields['instance']._choices),
                         2)
        self.assertEqual(res.status_code, 200)
        self.assertTrue(isinstance(form.fields['device'].widget,
                                   widgets.TextInput))

    @test.create_stubs({cinder: ('volume_get',), api.nova: ('server_list',)})
    def test_edit_attachments_cannot_set_mount_point(self):
        PREV = settings.OPENSTACK_HYPERVISOR_FEATURES['can_set_mount_point']
        settings.OPENSTACK_HYPERVISOR_FEATURES['can_set_mount_point'] = False

        volume = self.volumes.first()
        servers = self.servers.list()

        cinder.volume_get(IsA(http.HttpRequest), volume.id).AndReturn(volume)
        api.nova.server_list(IsA(http.HttpRequest)).AndReturn(servers)
        self.mox.ReplayAll()

        url = reverse('horizon:project:volumes:attach', args=[volume.id])
        res = self.client.get(url)
        # Assert the device field is hidden.
        form = res.context['form']
        self.assertTrue(isinstance(form.fields['device'].widget,
                                   widgets.HiddenInput))
        settings.OPENSTACK_HYPERVISOR_FEATURES['can_set_mount_point'] = PREV

    @test.create_stubs({cinder: ('volume_get',),
                        api.nova: ('server_get', 'server_list',)})
    def test_edit_attachments_attached_volume(self):
        server = self.servers.first()
        volume = self.volumes.list()[0]

        cinder.volume_get(IsA(http.HttpRequest), volume.id) \
                          .AndReturn(volume)
        api.nova.server_list(IsA(http.HttpRequest)) \
                             .AndReturn(self.servers.list())

        self.mox.ReplayAll()

        url = reverse('horizon:project:volumes:attach',
                      args=[volume.id])
        res = self.client.get(url)

        self.assertEqual(res.context['form'].fields['instance']._choices[0][1],
                         "Select an instance")
        self.assertEqual(len(res.context['form'].fields['instance'].choices),
                         2)
        self.assertEqual(res.context['form'].fields['instance']._choices[1][0],
                         server.id)
        self.assertEqual(res.status_code, 200)

    @test.create_stubs({cinder: ('volume_get',),
                        api.nova: ('server_get',)})
    def test_detail_view(self):
        volume = self.volumes.first()
        server = self.servers.first()

        volume.attachments = [{"server_id": server.id}]

        cinder.volume_get(IsA(http.HttpRequest), volume.id).AndReturn(volume)
        api.nova.server_get(IsA(http.HttpRequest), server.id).AndReturn(server)

        self.mox.ReplayAll()

        url = reverse('horizon:project:volumes:detail',
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
                            ("<a href=\"/project/instances/1/\">%s</a>"
                             % server.name),
                            1,
                            200)

        self.assertNoMessages()

    @test.create_stubs({cinder: ('volume_get',)})
    def test_get_data(self):
        volume = self.volumes.first()
        volume.display_name = ''

        cinder.volume_get(IsA(http.HttpRequest), volume.id).AndReturn(volume)

        self.mox.ReplayAll()

        url = reverse('horizon:project:volumes:index') + \
                "?action=row_update&table=volumes&obj_id=" + volume.id

        res = self.client.get(url, {},
                               HTTP_X_REQUESTED_WITH='XMLHttpRequest')

        self.assertEqual(res.status_code, 200)
        self.assertEqual(volume.display_name, volume.id)
