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
import logging


from django import shortcuts
from django.conf import settings
from django import forms 
from django.core.urlresolvers import reverse
from django.utils.translation import ugettext_lazy as _

from horizon import exceptions
from horizon import forms
from horizon import messages
from horizon.utils import functions as utils
from openstack_dashboard import api

from PIL import Image

LOG = logging.getLogger('idm_logger')

AVATAR = settings.MEDIA_ROOT+"/"+"OrganizationAvatar/"

class CreateOrganizationForm(forms.SelfHandlingForm):
    name = forms.CharField(label=_("Name"), max_length=64, required=True)
    description = forms.CharField(label=_("Description"), widget=forms.widgets.Textarea, required=True)
    enabled = forms.BooleanField(label=_("Enabled"), required=False, initial=True, widget=forms.HiddenInput())
    

    def handle(self, request, data):
        #create organization
        default_domain = api.keystone.get_default_domain(request)
        try:
            img = "/static/dashboard/img/logos/small/group.png" 
            city = ""
            email = ""
            website = ""       
            desc = data['description']
            self.object = api.keystone.tenant_create(request,
                                                name=data['name'],
                                                description=desc,
                                                enabled=data['enabled'],
                                                domain=default_domain,
                                                img=img,
                                                city=city,
                                                email=email,
                                                website=website)
        except Exception:
            exceptions.handle(request, ignore=True)
            return False

        #Set organization and user id
        organization_id = self.object.id
        user_id = request.user.id

        LOG.debug('Organization {0} created'.format(organization_id))

        #Find default role id
        try:
            default_role = api.keystone.get_default_role(self.request)
            if default_role is None:
                default = getattr(settings,
                                    "OPENSTACK_KEYSTONE_DEFAULT_ROLE", None)
                msg = _('Could not find default role "%s" in Keystone') % \
                        default
                LOG.debug(msg)
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
            LOG.debug('Added user {0} and organization {1} to role {2}'.format(user_id, organization_id, default_role.id))
        except Exception:
            exceptions.handle(request,
                                    _('Failed to add %s organization to list')
                                    % data['name'])
            return False
    
        response = shortcuts.redirect('horizon:idm:organizations:index')
        return response


class InfoForm(forms.SelfHandlingForm):
    orgID = forms.CharField(label=_("ID"), widget=forms.HiddenInput())
    name = forms.CharField(label=_("Name"), max_length=64, required=False)
    description = forms.CharField(label=_("Description"), widget=forms.widgets.Textarea, required=False)
    city = forms.CharField(label=_("City"), max_length=64, required=False)

    def handle(self, request, data):
        try:
            api.keystone.tenant_update(request, data['orgID'], name=data['name'], description=data['description'], city=data['city'])
            LOG.debug('Organization {0} updated'.format(data['orgID']))
            messages.success(request, _("Organization updated successfully."))
            response = shortcuts.redirect('horizon:idm:organizations:detail', data['orgID'])
            return response
        except Exception:
            response = shortcuts.redirect('horizon:idm:organizations:detail', data['orgID'])
            return response

class ContactForm(forms.SelfHandlingForm):
    orgID = forms.CharField(label=_("ID"), widget=forms.HiddenInput())
    email = forms.EmailField(label=_("E-mail"), required=False)
    website = forms.URLField(label=_("Website"), required=False)

    def handle(self, request, data):
        api.keystone.tenant_update(request, data['orgID'], email=data['email'], website=data['website'])
        LOG.debug('Organization {0} updated'.format(data['orgID']))
        messages.success(request, _("Organization updated successfully."))
        response = shortcuts.redirect('horizon:idm:organizations:detail', data['orgID'])
        return response

class AvatarForm(forms.SelfHandlingForm):
    orgID = forms.CharField(label=_("ID"), widget=forms.HiddenInput())
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

            img = Image.open(image)

            x1 = int(x1)
            x2 = int(x2)
            y1 = int(y1)
            y2 = int(y2)

            output_img = img.crop((x1, y1, x2, y2))
            imageName = self.data['orgID']
        
            output_img.save(settings.MEDIA_ROOT + "/" + "OrganizationAvatar/" + imageName, 'JPEG')
            organization = api.keystone.tenant_get(request, data['orgID'])
            img=settings.MEDIA_URL+'OrganizationAvatar/'+imageName
            api.keystone.tenant_update(request, data['orgID'], img=img)
            LOG.debug('Organization {0} image updated'.format(organization.id))
            messages.success(request, _("Organization updated successfully."))

        response = shortcuts.redirect('horizon:idm:organizations:detail', data['orgID'])
        return response
        
class CancelForm(forms.SelfHandlingForm):
    orgID = forms.CharField(label=_("ID"), widget=forms.HiddenInput())
    name = forms.CharField(label=_("Name"), widget=forms.HiddenInput(), required=False)

    def handle(self, request, data):
        
        organization = api.keystone.tenant_get(request, data['orgID'])
        image = organization.img
        if "OrganizationAvatar" in image:
            os.remove(AVATAR + organization.id)
            LOG.debug('{0} deleted'.format(image))
        api.keystone.tenant_delete(request, organization)
        LOG.info('Organization {0} deleted'.format(organization.id))
        messages.success(request, _("Organization deleted successfully."))
        response = shortcuts.redirect('horizon:idm:organizations:index')
        return response


       

