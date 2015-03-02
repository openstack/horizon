# Copyright (C) 2014 Universidad Politecnica de Madrid
#
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

import os
import logging

from django import shortcuts
from django.conf import settings
from django import forms 
from django.core.urlresolvers import reverse

from horizon import exceptions
from horizon import forms
from horizon import messages
from horizon.utils import functions as utils
from openstack_dashboard import api
from openstack_dashboard import fiware_api
from openstack_dashboard.local import local_settings
from openstack_dashboard.dashboards.idm import forms as idm_forms


LOG = logging.getLogger('idm_logger')
AVATAR_SMALL = settings.MEDIA_ROOT+"/"+"OrganizationAvatar/small/"
AVATAR_MEDIUM = settings.MEDIA_ROOT+"/"+"OrganizationAvatar/medium/"
AVATAR_ORIGINAL = settings.MEDIA_ROOT+"/"+"OrganizationAvatar/original/"

GENERIC_ERROR_MESSAGE = 'An error ocurred. Please try again later.'


class CreateOrganizationForm(forms.SelfHandlingForm):
    name = forms.CharField(label=("Name"), max_length=64, required=True)
    description = forms.CharField(
        label=("Description"), 
        widget=forms.widgets.Textarea(attrs={'rows':4, 'cols':40}),
        required=True)

    def clean_name(self):
        """ Validate that the name is not already in use."""
        org_name = self.cleaned_data['name']
        try:
            all_organizations, more = api.keystone.tenant_list(self.request)
            names_in_use = [org.name for org 
                             in all_organizations]
            if org_name in names_in_use:
                raise forms.ValidationError(
                    ("An organization with that name already exists."),
                    code='invalid')
            return org_name
        except Exception:
            exceptions.handle(self.request, 
                              GENERIC_ERROR_MESSAGE, 
                              ignore=True)

    def handle(self, request, data):
        #create organization
        default_domain = api.keystone.get_default_domain(request)
        try:
            city = ""
            email = ""
            website = ""
            self.object = api.keystone.tenant_create(
                request,
                name=data['name'],
                description=data['description'],
                enabled=True,
                domain=default_domain,
                city=city,
                email=email,
                website=website)
                                                     
        except Exception:
            exceptions.handle(request, 
                              GENERIC_ERROR_MESSAGE, 
                              ignore=True)
            return False

        #Set organization and user id
        organization_id = self.object.id
        user_id = request.user.id

        LOG.debug('Organization {0} created'.format(organization_id))

        #Find owner role id
        try:
            owner_role = fiware_api.keystone.get_owner_role(self.request)
            LOG.debug(owner_role)
            if owner_role is None:
                owner = getattr(local_settings,
                                    "KEYSTONE_OWNER_ROLE", None)
                msg = ('Could not find default role "%s" in Keystone') % \
                        default
                LOG.debug(msg)
                raise exceptions.NotFound(msg)
        except Exception as e:
            exceptions.handle(self.request,
                                redirect=reverse('horizon:idm:organizations:index'))
            return False
        try:
            api.keystone.add_tenant_user_role(request,
                                            project=organization_id,
                                            user=user_id,
                                            role=owner_role.id)
            LOG.debug('Added user {0} and organization {1} to role {2}'.format(user_id, organization_id, owner_role.id))
        except Exception:
            exceptions.handle(request,
                                    ('Failed to add %s organization to list')
                                    % data['name'])
            return False
    
        response = shortcuts.redirect('horizon:idm:organizations:index')
        return response


class InfoForm(forms.SelfHandlingForm):
    orgID = forms.CharField(label=("ID"), widget=forms.HiddenInput())
    name = forms.CharField(label=("Name"), max_length=64, required=True)
    description = forms.CharField(
        label=("Description"), 
        widget=forms.widgets.Textarea(attrs={'rows':4, 'cols':40}), 
        required=True)
    city = forms.CharField(label=("City"), max_length=64, required=False)
    title = 'Information'

    def handle(self, request, data):
        try:
            api.keystone.tenant_update(request, 
                                    data['orgID'], 
                                    name=data['name'], 
                                    description=data['description'], 
                                    city=data['city'])

            LOG.debug('Organization {0} updated'.format(data['orgID']))
            messages.success(request, ("Organization updated successfully."))
            response = shortcuts.redirect('horizon:idm:organizations:detail', data['orgID'])
            return response
        except Exception:
            response = shortcuts.redirect('horizon:idm:organizations:detail', data['orgID'])
            return response

class ContactForm(forms.SelfHandlingForm):
    orgID = forms.CharField(label=("ID"), widget=forms.HiddenInput())
    email = forms.EmailField(label=("E-mail"), required=False)
    website = forms.URLField(label=("Website"), required=False)
    title = 'Contact Information'

    def handle(self, request, data):
        api.keystone.tenant_update(request, 
                                data['orgID'], 
                                email=data['email'], 
                                website=data['website'])
        LOG.debug('Organization {0} updated'.format(data['orgID']))
        messages.success(request, ("Organization updated successfully."))
        response = shortcuts.redirect('horizon:idm:organizations:detail', data['orgID'])
        return response


class AvatarForm(forms.SelfHandlingForm, idm_forms.ImageCropMixin):
    orgID = forms.CharField(label=("ID"), widget=forms.HiddenInput())
    image = forms.ImageField(required=False)
    title = 'Avatar Update'

    def handle(self, request, data):
        if request.FILES:
            image = request.FILES['image'] 
            output_img = self.crop(image)
            
            small = 25, 25, 'small'
            medium = 36, 36, 'medium'
            original = 100, 100, 'original'
            meta = [original, medium, small]
            for meta in meta:
                size = meta[0], meta[1]
                img_type = meta[2]
                output_img.thumbnail(size)
                img = 'OrganizationAvatar/' + img_type + "/" + self.data['orgID']
                output_img.save(settings.MEDIA_ROOT + "/" + img, 'JPEG')
        
                if img_type == 'small':
                    api.keystone.tenant_update(request, data['orgID'], img_small=img)
                elif img_type == 'medium':
                    api.keystone.tenant_update(request, data['orgID'], img_medium=img)
                else:
                    api.keystone.tenant_update(request, data['orgID'], img_original=img)

            LOG.debug('Organization {0} image updated'.format(data['orgID']))
            messages.success(request, ("Organization updated successfully."))

        response = shortcuts.redirect('horizon:idm:organizations:detail', data['orgID'])
        return response

             
class CancelForm(forms.SelfHandlingForm):
    orgID = forms.CharField(label=("ID"), widget=forms.HiddenInput())
    title = 'Cancel'
    
    def handle(self, request, data, organization):
        image = getattr(organization,'img_original','')
        if "OrganizationAvatar" in image:
            os.remove(AVATAR_SMALL + organization.id)
            os.remove(AVATAR_MEDIUM + organization.id)
            os.remove(AVATAR_ORIGINAL + organization.id)
            LOG.debug('{0} deleted'.format(image))
        api.keystone.tenant_delete(request, organization)
        LOG.info('Organization {0} deleted'.format(organization.id))
        messages.success(request, ("Organization deleted successfully."))
        response = shortcuts.redirect('horizon:idm:organizations:index')
        return response
