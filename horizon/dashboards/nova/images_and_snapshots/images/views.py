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

"""
Views for managing Nova images.
"""

import logging
from django.core.urlresolvers import reverse
from django.utils.translation import ugettext_lazy as _

from horizon import api
from horizon import exceptions
from horizon import forms
from horizon import tabs
from .forms import UpdateImageForm, LaunchForm
from .tabs import ImageDetailTabs


LOG = logging.getLogger(__name__)


class LaunchView(forms.ModalFormView):
    form_class = LaunchForm
    template_name = 'nova/images_and_snapshots/images/launch.html'
    context_object_name = 'image'

    def get_form_kwargs(self):
        kwargs = super(LaunchView, self).get_form_kwargs()
        kwargs['flavor_list'] = self.flavor_list()
        kwargs['keypair_list'] = self.keypair_list()
        kwargs['security_group_list'] = self.security_group_list()
        kwargs['volume_list'] = self.volume_list()
        return kwargs

    def get_object(self, *args, **kwargs):
        image_id = self.kwargs["image_id"]
        try:
            self.object = api.image_get_meta(self.request, image_id)
        except:
            msg = _('Unable to retrieve image "%s".') % image_id
            redirect = reverse('horizon:nova:images_and_snapshots:index')
            exceptions.handle(self.request, msg, redirect=redirect)
        return self.object

    def get_context_data(self, **kwargs):
        context = super(LaunchView, self).get_context_data(**kwargs)
        try:
            context['usages'] = api.tenant_quota_usages(self.request)
        except:
            exceptions.handle(self.request)
        return context

    def get_initial(self):
        return {'image_id': self.kwargs["image_id"],
                'tenant_id': self.request.user.tenant_id}

    def flavor_list(self):
        display = '%(name)s (%(vcpus)sVCPU / %(disk)sGB Disk / %(ram)sMB Ram )'
        try:
            flavors = api.flavor_list(self.request)
            flavor_list = [(flavor.id, display % {"name": flavor.name,
                                                  "vcpus": flavor.vcpus,
                                                  "disk": flavor.disk,
                                                  "ram": flavor.ram})
                                                for flavor in flavors]
        except:
            flavor_list = []
            exceptions.handle(self.request,
                              _('Unable to retrieve instance flavors.'))
        return sorted(flavor_list)

    def keypair_list(self):
        try:
            keypairs = api.keypair_list(self.request)
            keypair_list = [(kp.name, kp.name) for kp in keypairs]
        except:
            keypair_list = []
            exceptions.handle(self.request,
                              _('Unable to retrieve keypairs.'))
        return keypair_list

    def security_group_list(self):
        try:
            groups = api.security_group_list(self.request)
            security_group_list = [(sg.name, sg.name) for sg in groups]
        except:
            exceptions.handle(self.request,
                              _('Unable to retrieve list of security groups'))
            security_group_list = []
        return security_group_list

    def volume_list(self):
        volume_options = [("", _("Select Volume"))]

        def _get_volume_select_item(volume):
            if hasattr(volume, "volume_id"):
                vol_type = "snap"
                visible_label = _("Snapshot")
            else:
                vol_type = "vol"
                visible_label = _("Volume")
            return (("%s:%s" % (volume.id, vol_type)),
                    ("%s - %s GB (%s)" % (volume.display_name,
                                         volume.size,
                                         visible_label)))

        # First add volumes to the list
        try:
            volumes = [v for v in api.volume_list(self.request) \
                       if v.status == api.VOLUME_STATE_AVAILABLE]
            volume_options.extend(
                    [_get_volume_select_item(vol) for vol in volumes])
        except:
            exceptions.handle(self.request,
                              _('Unable to retrieve list of volumes'))

        # Next add volume snapshots to the list
        try:
            snapshots = api.volume_snapshot_list(self.request)
            snapshots = [s for s in snapshots \
                         if s.status == api.VOLUME_STATE_AVAILABLE]
            volume_options.extend(
                    [_get_volume_select_item(snap) for snap in snapshots])
        except:
            exceptions.handle(self.request,
                              _('Unable to retrieve list of volumes'))

        return volume_options


class UpdateView(forms.ModalFormView):
    form_class = UpdateImageForm
    template_name = 'nova/images_and_snapshots/images/update.html'
    context_object_name = 'image'

    def get_object(self, *args, **kwargs):
        try:
            self.object = api.image_get_meta(self.request, kwargs['image_id'])
        except:
            msg = _('Unable to retrieve image "%s".') % kwargs['image_id']
            redirect = reverse('horizon:nova:images_and_snapshots:index')
            exceptions.handle(self.request, msg, redirect=redirect)
        return self.object

    def get_initial(self):
        properties = self.object['properties']
        return {'image_id': self.kwargs['image_id'],
                'name': self.object.get('name', ''),
                'kernel': properties.get('kernel_id', ''),
                'ramdisk': properties.get('ramdisk_id', ''),
                'architecture': properties.get('architecture', ''),
                'container_format': self.object.get('container_format', ''),
                'disk_format': self.object.get('disk_format', ''), }


class DetailView(tabs.TabView):
    tab_group_class = ImageDetailTabs
    template_name = 'nova/images_and_snapshots/images/detail.html'
