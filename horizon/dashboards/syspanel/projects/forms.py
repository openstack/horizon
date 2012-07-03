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

import logging

from django.utils.translation import ugettext_lazy as _

from horizon import api
from horizon import exceptions
from horizon import forms
from horizon import messages


LOG = logging.getLogger(__name__)


class AddUser(forms.SelfHandlingForm):
    tenant_id = forms.CharField(widget=forms.widgets.HiddenInput())
    user_id = forms.CharField(widget=forms.widgets.HiddenInput())
    role_id = forms.ChoiceField(label=_("Role"))

    def __init__(self, *args, **kwargs):
        roles = kwargs.pop('roles')
        super(AddUser, self).__init__(*args, **kwargs)
        role_choices = [(role.id, role.name) for role in roles]
        self.fields['role_id'].choices = role_choices

    def handle(self, request, data):
        try:
            api.add_tenant_user_role(request,
                                     data['tenant_id'],
                                     data['user_id'],
                                     data['role_id'])
            messages.success(request, _('Successfully added user to project.'))
            return True
        except:
            exceptions.handle(request, _('Unable to add user to project.'))
