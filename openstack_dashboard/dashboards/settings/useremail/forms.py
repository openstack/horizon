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

from django import shortcuts
from django.conf import settings
from django.contrib import auth as django_auth

from django.views.decorators.debug import sensitive_variables  # noqa

from horizon import exceptions
from horizon import forms
from horizon import messages
from horizon.utils import functions as utils

from openstack_dashboard import api
from openstack_auth import exceptions as auth_exceptions


LOG = logging.getLogger('idm_logger')

class EmailForm(forms.SelfHandlingForm):
    email = forms.EmailField(
            label=("Email"),
            required=True)
    password = forms.CharField(
            label=("Current password"),
            widget=forms.PasswordInput(render_value=False),
            required=True)

    # We have to protect the entire "data" dict because it contains the
    # password string.
    @sensitive_variables('data')
    def handle(self, request, data):
        # the user's password to change the email, only to update the password
        user_is_editable = api.keystone.keystone_can_edit_user()
        if user_is_editable:
            try:
                # check if the password is correct
                password = data['password']
                domain = getattr(settings,
                                'OPENSTACK_KEYSTONE_DEFAULT_DOMAIN',
                                'Default')
                default_region = (settings.OPENSTACK_KEYSTONE_URL, "Default Region")
                region = getattr(settings, 'AVAILABLE_REGIONS', [default_region])[0][0]

                name = request.user.name
                result = django_auth.authenticate(request=request,
                                    username=name,
                                    password=password,
                                    user_domain_name=domain,
                                    auth_url=region)

                # now update email
                user_id = request.user.id
                #user = api.keystone.user_get(request, user_id, admin=False)
                
                # if we dont set password to None we get a dict-key error in api/keystone
                api.keystone.user_update(request, user_id, name=data['email'],
                                        password=None)
                
                # redirect user to settings home
                response = shortcuts.redirect('horizon:settings:multisettings:index')
                #response = shortcuts.redirect(request.build_absolute_uri())
                #response = shortcuts.redirect(horizon.get_user_home(request.user))
                msg = ("Email changed succesfully")
                LOG.debug(msg)
                messages.success(request, msg)
                return response

            except auth_exceptions.KeystoneAuthException as exc:
                messages.error(request, ('Invalid password'))
                LOG.error(exc)
                return False
            except Exception as e:
                exceptions.handle(request,
                                  ('Unable to change email.'))
                LOG.error(e)
                return False
        else:
            messages.error(request, ('Changing email is not supported.'))
            LOG.debug("Changing email is not supported")
            return False
