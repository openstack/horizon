# Copyright 2012 United States Government as represented by the
# Administrator of the National Aeronautics and Space Administration.
# All Rights Reserved.
#
# Copyright 2012 OpenStack Foundation
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
import os

from django import shortcuts
from django.conf import settings
from django import forms 
from django.utils.translation import ugettext_lazy as _

from horizon import exceptions
from horizon import forms
from horizon import messages
from horizon.utils import functions as utils
from openstack_dashboard import api

from PIL import Image

AVATAR_ROOT = os.path.abspath(os.path.join(settings.MEDIA_ROOT, 'OrganizationAvatars'))

class CreateOrganizationForm(forms.SelfHandlingForm):
    name = forms.CharField(label=_("Name"), max_length=64, required=True)
    description = forms.CharField(label=_("Description"), widget=forms.widgets.Textarea, required=True)
    enabled = forms.BooleanField(label=_("Enabled"), required=False, initial=True, widget=forms.HiddenInput())
    

    def handle(self, request, data):
    	#create organization
    	default_domain = api.keystone.get_default_domain(request)
    	try:
    		desc = data['description']
    		self.object = api.keystone.tenant_create(request,
    											name=data['name'],
    											description=desc,
    											enabled=data['enabled'],
    											domain=default_domain)
    	except Exception:
    		exceptions.handle(request, ignore=True)
    		return False

    	#Set organization and user id
    	organization_id = self.object.id
    	user_id = request.user.id

    	#Find default role id
    	try:
    		default_role = api.keystone.get_default_role(self.request)
    		if default_role is None:
    			default = getattr(settings,
    								"OPENSTACK_KEYSTONE_DEFAULT_ROLE", None)
    			msg = _('Could not find default role "%s" in Keystone') % \
    					default
    			raise exceptions.NotFound(msg)
    	except Exception as e:
    		exceptions.handle(self.request, 
    							e.error,
    							redirect=reverse('horizon:idm:organizations:index'))
    		return False
    	try:
    		api.keystone.add_tenant_user_role(request,
    										project=organization_id,
    										user=user_id,
    										role=default_role.id)
    	except Exception:
    		exceptions.handle(request,
    								_('Failed to add %s organization to list')
    								% data['name'])
    		return False
    
       	response = shortcuts.redirect('horizon:idm:organizations:index')
    	return response

# class EditOrganizationForm(forms.SelfHandlingForm):
#     orgID = forms.CharField(label=_("ID"), widget=forms.HiddenInput())
#     name = forms.CharField(label=_("Name"), max_length=64,required=False)
#     description = forms.CharField(label=_("Description"),widget=forms.widgets.Textarea, required=False)
#     city = forms.CharField(label=_("City"), max_length=64,required=False)
#     email = forms.EmailField(label=_("E-mail"),required=False)
#     website=forms.URLField(label=_("Website"),required=False)
#     image = forms.ImageField(required=False)
#     x1 = forms.DecimalField(widget=forms.HiddenInput(), required=False)
#     y1 = forms.DecimalField(widget=forms.HiddenInput(), required=False)
#     x2 = forms.DecimalField(widget=forms.HiddenInput(), required=False)
#     y2 = forms.DecimalField(widget=forms.HiddenInput(), required=False)


#     def handle(self, request, data):
#         try:
#             if '_edit' in request.POST:
#                 if request.FILES:

#                     x1=self.cleaned_data['x1']
#                     x2=self.cleaned_data['x2']
#                     y1=self.cleaned_data['y1']
#                     y2=self.cleaned_data['y2']
                   
#                     image = request.FILES['image']
#                     avatarName = data['name']

#                     img = Image.open(image)

#                     import pdb
#                     pdb.set_trace()

#                     x1 = int(x1)
#                     x2 = int(x2)
#                     y1 = int(y1)
#                     y2 = int(y2)
                
#                     output_img = img.crop((x1,y1,x2,y2))
#                     output_img.save(settings.MEDIA_ROOT+"/"+"OrganizationAvatar/"+avatarName, 'JPEG')

#                     messages.success(request, _("Organization updated successfully."))
#                     response = shortcuts.redirect('horizon:idm:organizations:index')
#                     return response
#                 else:
#                     try:
#                         api.keystone.tenant_update(request, data['orgID'], name=data['name'], description=data['description'])
#                         messages.success(request, _("Organization updated successfully."))
#                         response = shortcuts.redirect('horizon:idm:organizations:index')
#                         return response
#                     except Exception:
#                         response = shortcuts.redirect('horizon:idm:organizations:index')
#                         return response
#             elif '_delete' in request.POST:
#                 organization = data['orgID']
#                 api.keystone.tenant_delete(request, organization)
#                 messages.success(request, _("Organization deleted successfully."))
#                 response = shortcuts.redirect('horizon:idm:organizations:index')
#                 return response
#         except Exception:
#             exceptions.handle(request, _('Unable to update organization.'))

class InfoForm(forms.SelfHandlingForm):
    action="url1/"
    title = 'Information'
    orgID = forms.CharField(label=_("ID"), widget=forms.HiddenInput())
    name = forms.CharField(label=_("Name"), max_length=64,required=False)
    description = forms.CharField(label=_("Description"),widget=forms.widgets.Textarea, required=False)
    city = forms.CharField(label=_("City"), max_length=64,required=False)

    def handle(self, request, data):
        try:
            print('entra al handle')
            api.keystone.tenant_update(request, data['orgID'], name=data['name'], description=data['description'])
            messages.success(request, _("Organization updated successfully."))
            response = shortcuts.redirect('horizon:idm:myApplications:index')
            return response
        except Exception:
            response = shortcuts.redirect('horizon:idm:myApplications:index')
            return response

class ContactForm(forms.SelfHandlingForm):
    action="url2/"
    title = 'Contact Information'
    orgID = forms.CharField(label=_("ID"), widget=forms.HiddenInput())
    email = forms.EmailField(label=_("E-mail"),required=False)
    website=forms.URLField(label=_("Website"),required=False)

    def handle(self, requestm, data):
        response = shortcuts.redirect('horizon:idm:organizations:index')
        return response

# class AvatarForm(forms.SelfHandlingForm):
#     # action="url3/"
#     # title = 'Avatar Update'
#     orgID = forms.CharField(label=_("ID"), widget=forms.HiddenInput())
#     name = forms.CharField(label=_("Name"), widget=forms.HiddenInput(),required=False)
#     image = forms.ImageField(required=False)
#     x1 = forms.DecimalField(widget=forms.HiddenInput(), required=False)
#     y1 = forms.DecimalField(widget=forms.HiddenInput(), required=False)
#     x2 = forms.DecimalField(widget=forms.HiddenInput(), required=False)
#     y2 = forms.DecimalField(widget=forms.HiddenInput(), required=False)

#     def handle(self, requestm, data):
#         x1=self.cleaned_data['x1']
#         x2=self.cleaned_data['x2']
#         y1=self.cleaned_data['y1']
#         y2=self.cleaned_data['y2']

#         image = request.FILES['image']
#         avatarName = data['name']

#         img = Image.open(image)

#         x1 = int(x1)
#         x2 = int(x2)
#         y1 = int(y1)
#         y2 = int(y2)

#         output_img = img.crop((x1,y1,x2,y2))
#         output_img.save(settings.MEDIA_ROOT+"/"+"OrganizationAvatar/"+avatarName, 'JPEG')

#         messages.success(request, _("Organization updated successfully."))
#         response = shortcuts.redirect('horizon:idm:organizations:index')
#         return response
        
# class CancelForm(forms.SelfHandlingForm):
#     # action="url4/"
#     # title = 'Cancel'
#     orgID = forms.CharField(label=_("ID"), widget=forms.HiddenInput())
#     name = forms.CharField(label=_("Name"), widget=forms.HiddenInput(),required=False)

#     def handle(self, requestm, data):
#         organization = data['orgID']
#         api.keystone.tenant_delete(request, organization)
#         messages.success(request, _("Organization deleted successfully."))
#         response = shortcuts.redirect('horizon:idm:organizations:index')
#         return response
        


