# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

import logging
import os
from PIL import Image 

from django import shortcuts
from django.conf import settings
from django import forms
from django.utils.translation import ugettext_lazy as _

from horizon import exceptions
from horizon import forms
from horizon.utils import functions as utils
from horizon import messages

from openstack_dashboard import fiware_api

LOG = logging.getLogger(__name__)
DEFAULT_AVATAR = os.path.abspath(os.path.join(settings.ROOT_PATH, '..', 
            'openstack_dashboard/static/dashboard/img/logos/original/group.png'))


class CreateApplicationForm(forms.SelfHandlingForm):
    name = forms.CharField(label=_("Name"), required=False)
    description = forms.CharField(label=_("Description"), 
                                widget=forms.Textarea, 
                                required=False)
    url = forms.CharField(label=_("URL"), required=False)
    callbackurl = forms.CharField(label=_("Callback URL"), required=False)

    def handle(self, request, data):
        response = shortcuts.redirect('horizon:idm:myApplications:upload')
        return response
    
class UploadImageForm(forms.SelfHandlingForm):
    image = forms.ImageField(required=False)
    x1 = forms.DecimalField(widget=forms.HiddenInput(), required=False)
    y1 = forms.DecimalField(widget=forms.HiddenInput(), required=False)
    x2 = forms.DecimalField(widget=forms.HiddenInput(), required=False)
    y2 = forms.DecimalField(widget=forms.HiddenInput(), required=False)
        
    def handle(self, request, data):
        if request.FILES:
            x1 = self.cleaned_data['x1'] 
            x2 = self.cleaned_data['x2']
            y1 = self.cleaned_data['y1']
            y2 = self.cleaned_data['y2']

            image = request.FILES['image'] 
            imageName = image.name
            
            img = Image.open(image)

            x1 = int(x1)
            x2 = int(x2)
            y1 = int(y1)
            y2 = int(y2)

            output_img = img.crop((x1, y1, x2, y2))
        else:
            output_img = Image.open(DEFAULT_AVATAR)
            imageName = 'avatarApp'
            
        output_img.save(settings.MEDIA_ROOT+"/"+"ApplicationAvatar/"+imageName, 'JPEG')

        response = shortcuts.redirect('horizon:idm:myApplications:roles_index')
        return response


class CreateRoleForm(forms.SelfHandlingForm):
    # application_id = forms.CharField(label=_("Domain ID"),
    #                             required=True,
    #                             widget=forms.HiddenInput())
    name = forms.CharField(max_length=255, label=_("Role Name"))
    no_autocomplete = True

    def handle(self, request, data):
        try:
            LOG.info('Creating role with name "%s"' % data['name'])
            new_role = fiware_api.keystone.role_create(request,
                                                name=data['name'])
            messages.success(request,
                             _('Role "%s" was successfully created.')
                             % data['name'])
            return new_role
        except Exception:
            exceptions.handle(request, _('Unable to create role.'))


class CreatePermissionForm(forms.SelfHandlingForm):
    # application_id = forms.CharField(label=_("Domain ID"),
    #                             required=True,
    #                             widget=forms.HiddenInput())
    name = forms.CharField(max_length=255, label=_("Permission Name"))
    no_autocomplete = True

    def handle(self, request, data):
        try:
            LOG.info('Creating permission with name "%s"' % data['name'])
            new_permission = fiware_api.keystone.permission_create(request,
                                                name=data['name'])
            messages.success(request,
                             _('Permission "%s" was successfully created.')
                             % data['name'])
            return new_permission
        except Exception:
            exceptions.handle(request, _('Unable to create permission.'))