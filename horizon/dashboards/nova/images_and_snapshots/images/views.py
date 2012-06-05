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
from .forms import UpdateImageForm
from .forms import CreateImageForm
from .tabs import ImageDetailTabs


LOG = logging.getLogger(__name__)


class CreateView(forms.ModalFormView):
    form_class = CreateImageForm
    template_name = 'nova/images_and_snapshots/images/create.html'
    context_object_name = 'image'


class UpdateView(forms.ModalFormView):
    form_class = UpdateImageForm
    template_name = 'nova/images_and_snapshots/images/update.html'
    context_object_name = 'image'

    def get_object(self, *args, **kwargs):
        try:
            self.object = api.image_get(self.request, kwargs['image_id'])
        except:
            msg = _('Unable to retrieve image.')
            redirect = reverse('horizon:nova:images_and_snapshots:index')
            exceptions.handle(self.request, msg, redirect=redirect)
        return self.object

    def get_initial(self):
        properties = self.object.properties
        # NOTE(gabriel): glanceclient currently treats "is_public" as a string
        # rather than a boolean. This should be fixed in the client.
        public = self.object.is_public == "True"
        return {'image_id': self.kwargs['image_id'],
                'name': self.object.name,
                'kernel': properties.get('kernel_id', ''),
                'ramdisk': properties.get('ramdisk_id', ''),
                'architecture': properties.get('architecture', ''),
                'container_format': self.object.container_format,
                'disk_format': self.object.disk_format,
                'public': public}


class DetailView(tabs.TabView):
    tab_group_class = ImageDetailTabs
    template_name = 'nova/images_and_snapshots/images/detail.html'
