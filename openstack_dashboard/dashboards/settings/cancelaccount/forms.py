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
from django import shortcuts
import horizon
from horizon import exceptions
from horizon import forms
from horizon import messages

from openstack_dashboard import api


class BasicCancelForm(forms.SelfHandlingForm):

    def handle(self, request, data):
        #the user's password to change the email, only to update the password
        user_is_editable = api.keystone.keystone_can_edit_user()
        if user_is_editable:
            try:
                user_id=request.user.id
                user = api.keystone.user_get(request,user_id)
                api.keystone.user_update_enabled(request,user,enabled=False)
                msg = _("Account canceled succesfully")
                messages.success(request,msg)
                #Log the user out
                endpoint = request.session.get('region_endpoint')
                token = request.session.get('token')
                if token and endpoint:
                    delete_token(endpoint=endpoint, token_id=token.id)
                    
                response = shortcuts.redirect(horizon.get_user_home(request.user))
                return response 
            except Exception:   
                exceptions.handle(request,
                                  _('Unable to cancel account.'))
                return False
        else:
            messages.error(request, _('Account canceling is not supported.'))
            return False
