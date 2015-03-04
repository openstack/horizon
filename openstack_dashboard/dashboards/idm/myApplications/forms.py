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

import logging
import os

from django import forms
from django import shortcuts
from django.conf import settings
from django.http import HttpResponse

from horizon import exceptions
from horizon import forms
from horizon import messages
from horizon.utils import functions as utils

from openstack_dashboard import fiware_api
from openstack_dashboard import api
from openstack_dashboard.dashboards.idm import forms as idm_forms
from openstack_dashboard.local import local_settings


LOG = logging.getLogger('idm_logger')
AVATAR_SMALL = settings.MEDIA_ROOT+"/ApplicationAvatar/small/"
AVATAR_MEDIUM = settings.MEDIA_ROOT+"/ApplicationAvatar/medium/"
AVATAR_ORIGINAL = settings.MEDIA_ROOT+"/ApplicationAvatar/original/"

class CreateApplicationForm(forms.SelfHandlingForm):
    appID = forms.CharField(widget=forms.HiddenInput(), required=False)
    redirect_to = forms.CharField(widget=forms.HiddenInput(), required=False)
    name = forms.CharField(label=("Name"), required=True)
    description = forms.CharField(
        label=("Description"), 
        widget=forms.Textarea(attrs={'rows':4, 'cols':40}),
        required=True)
    url = forms.CharField(label=("URL"), required=True)
    callbackurl = forms.CharField(label=("Callback URL"), required=True)
    title = 'Information'

    def handle(self, request, data):
        #create application
        #default_domain = api.keystone.get_default_domain(request)
        if data['redirect_to'] == "create":
            try:
                application = fiware_api.keystone.application_create(request,
                                                name=data['name'],
                                                description=data['description'],
                                                redirect_uris=[data['callbackurl']],
                                                url=data['url'])

                provider = fiware_api.keystone.get_provider_role(request)
                user = request.user
                organization = request.organization

                if request.organization.id == request.user.default_project_id:
                    fiware_api.keystone.add_role_to_user(request,
                                                         role=provider,
                                                         user=user,
                                                         organization=organization,
                                                         application=application)
                else:
                    fiware_api.keystone.add_role_to_organization(request,
                                                                 role=provider,
                                                                 organization=organization,
                                                                 application=application)
                LOG.debug('Application {0} created'.format(application.name))
            except Exception:
                exceptions.handle(
                    request, ('Unable to register the application.'))
                return False
            response = shortcuts.redirect(
                'horizon:idm:myApplications:avatar_step', application.id)


        else:
            try:
                LOG.debug('updating application {0}'.format(data['appID']))

                redirect_uris = [data['callbackurl'],]
                fiware_api.keystone.application_update(request, 
                                                data['appID'], 
                                                name=data['name'], 
                                                description=data['description'],
                                                redirect_uris=redirect_uris, 
                                                url=data['url'])
                msg = 'Application updated successfully.'
                messages.success(request, (msg))
                LOG.debug(msg)
                response = shortcuts.redirect(
                    'horizon:idm:myApplications:detail', data['appID'])
            except Exception as e:
                LOG.error(e)
                exceptions.handle(request, ('Unable to update the application.'))

        return response
    
    
class AvatarForm(forms.SelfHandlingForm, idm_forms.ImageCropMixin):
    appID = forms.CharField(widget=forms.HiddenInput())
    image = forms.ImageField(required=False)
    redirect_to = forms.CharField(widget=forms.HiddenInput(), required=False)
    title = 'Avatar Update'

    def handle(self, request, data):
        application_id = data['appID']
        if request.FILES:

            image = request.FILES['image'] 
            output_img = self.crop(image)
            
            small = 25, 25, 'small'
            medium = 36, 36, 'medium'
            original = 100, 100, 'original'

            # if output_img.size[0] < original[0]:
            #     messages.warning(request, 'Image is smaller than 60px/60px')
                
            meta = [original, medium, small]
            for meta in meta:
                size = meta[0], meta[1]
                img_type = meta[2]
                output_img.resize(size)
                img = (settings.MEDIA_ROOT +'/ApplicationAvatar/' 
                       + img_type + "/" + application_id)
                output_img.save(img, 'JPEG')
                image_root = ('ApplicationAvatar/' + img_type 
                              + "/" + application_id)
                if img_type == 'small':
                    fiware_api.keystone.application_update(
                        request, application_id, img_small=image_root)
                elif img_type == 'medium':
                    fiware_api.keystone.application_update(
                        request, application_id, img_medium=image_root)
                else:
                    fiware_api.keystone.application_update(
                        request, application_id, img_original=image_root)

        if data['redirect_to'] == "update":
            response = shortcuts.redirect(
                'horizon:idm:myApplications:detail', application_id) 
            LOG.debug('Avatar for application {0} updated'.format(application_id))
        else:
            response = shortcuts.redirect(
                'horizon:idm:myApplications:roles_step', application_id)
            LOG.debug('Avatar for application {0} saved'.format(application_id))
        return response


class CreateRoleForm(forms.SelfHandlingForm):
    name = forms.CharField(max_length=255, label=("Role Name"))
    application_id = forms.CharField(required=True,
                                     widget=forms.HiddenInput())
    no_autocomplete = True

    def handle(self, request, data):
        try:
            LOG.info('Creating role with name "%s"' % data['name'])
            new_role = fiware_api.keystone.role_create(
                request, name=data['name'], application=data['application_id'])
            messages.success(request,
                             ('Role "%s" was successfully created.')
                             % data['name'])
            return new_role
        except Exception:
            exceptions.handle(request, ('Unable to create role.'))


class EditRoleForm(forms.SelfHandlingForm):
    role_id = forms.CharField(required=True,
                              widget=forms.HiddenInput())
    name = forms.CharField(max_length=60, label='')
    no_autocomplete = True

    def handle(self, request, data):
        try:
            LOG.info('Updating role with id {0}'.format(data['role_id']))
            role = fiware_api.keystone.role_update(request,
                                            role=data['role_id'],
                                            name=data['name'])
            messages.success(request,
                             ('Role "%s" was successfully updated.')
                             % data['role_id'])
            response = HttpResponse(role.name)
            return response
        except Exception:
            exceptions.handle(request, ('Unable to delete role.'))


class DeleteRoleForm(forms.SelfHandlingForm):
    role_id = forms.CharField(required=True,
                              widget=forms.HiddenInput())

    def handle(self, request, data):
        try:
            LOG.info('Deleting role with id {0}'.format(data['role_id']))
            fiware_api.keystone.role_delete(request,
                                            role_id=data['role_id'])
            messages.success(request,
                             ('Role "%s" was successfully deleted.')
                             % data['role_id'])
            return True
        except Exception:
            exceptions.handle(request, ('Unable to delete role.'))


class CreatePermissionForm(forms.SelfHandlingForm):
    application_id = forms.CharField(required=True,
                                     widget=forms.HiddenInput())
    name = forms.CharField(max_length=255, label=("Permission Name"))
    description = forms.CharField(max_length=255, label=("Description"))
    action = forms.CharField(max_length=255, label=("HTTP action"))
    resource = forms.CharField(max_length=255, label=("Resource"))
    no_autocomplete = True

    def handle(self, request, data):
        try:
            LOG.info('Creating permission with name "%s"' % data['name'])
            new_permission = fiware_api.keystone.permission_create(
                request, name=data['name'], application=data['application_id'])
            # TODO(garcianavalon) add support for extra arguments in permissions
                                            # resource=data['resource'],
                                            # action=data['action'])

            messages.success(request,
                             ('Permission "%s" was successfully created.')
                             % data['name'])
            return new_permission
        except Exception:
            exceptions.handle(request, ('Unable to create permission.'))

        
class CancelForm(forms.SelfHandlingForm):
    appID = forms.CharField(label=("ID"), widget=forms.HiddenInput())
    title = 'Cancel'

    def handle(self, request, data, application):
        image = getattr(application, 'img_original', '')
        LOG.debug(image)
        if "ApplicationAvatar" in image:
            os.remove(AVATAR_SMALL + application.id)
            os.remove(AVATAR_MEDIUM + application.id)
            os.remove(AVATAR_ORIGINAL + application.id)
            LOG.debug('Avatar deleted from server')    
        fiware_api.keystone.application_delete(request, application.id)
        LOG.info('Application {0} deleted'.format(application.id))
        messages.success(request, ("Application deleted successfully."))
        response = shortcuts.redirect('horizon:idm:myApplications:index')
        return response