# Copyright 2013 Centrin Data Systems Ltd.
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

from django.utils.translation import ugettext_lazy as _
from django.views.decorators.debug import sensitive_variables  # noqa
from django import shortcuts

from horizon import exceptions
from horizon import forms
from horizon import messages
from horizon.utils import functions as utils

from openstack_dashboard import api


class EmailForm(forms.SelfHandlingForm):
    email = forms.EmailField(
            label=_("Email"),
            required=True)
    current_password = forms.CharField(label=_("Current password"),
                           widget=forms.PasswordInput(render_value=False))

    # We have to protect the entire "data" dict because it contains the
    # oldpassword string.
    @sensitive_variables('data')
    def handle(self, request, data):
        #TODO we are not doing anything with the password because horizon+keystone doesn't requiere
        #the user's password to change the email, only to update the password
        user_is_editable = api.keystone.keystone_can_edit_user()
        if user_is_editable:
            try:
                user_id=request.user.id
                user = api.keystone.user_get(request,user_id)
                something = api.keystone.user_update(request,user,email=data['email'])
                response = shortcuts.redirect(request.build_absolute_uri())
                msg = _("Email changed succesfully")
                return response
            except Exception:
                exceptions.handle(request,
                                  _('Unable to change email.'))
                return False
        else:
            messages.error(request, _('Changing email is not supported.'))
            return False
