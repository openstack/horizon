# Copyright 2012,  Nachi Ueno,  NTT MCL,  Inc.
# All rights reserved.

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

"""
Views for managing Neutron Routers.
"""
import logging

from django.core.urlresolvers import reverse
from django.core.urlresolvers import reverse_lazy
from django.utils.translation import ugettext_lazy as _

from horizon import exceptions
from horizon import forms
from horizon import messages

from openstack_dashboard import api

LOG = logging.getLogger(__name__)


class CreateForm(forms.SelfHandlingForm):
    name = forms.CharField(max_length="255", label=_("Router Name"))
    mode = forms.ChoiceField(label=_("Router Type"))
    failure_url = 'horizon:project:routers:index'

    def __init__(self, request, *args, **kwargs):
        super(CreateForm, self).__init__(request, *args, **kwargs)
        self.dvr_enabled = api.neutron.get_dvr_permission(self.request,
                                                          "create")
        if self.dvr_enabled:
            mode_choices = [('server_default', _('Use Server Default')),
                            ('centralized', _('Centralized')),
                            ('distributed', _('Distributed'))]
            self.fields['mode'].choices = mode_choices
        else:
            self.fields['mode'].widget = forms.HiddenInput()
            self.fields['mode'].required = False

    def handle(self, request, data):
        try:
            params = {'name': data['name']}
            if (self.dvr_enabled and data['mode'] != 'server_default'):
                params['distributed'] = (data['mode'] == 'distributed')
            router = api.neutron.router_create(request, **params)
            message = _('Router %s was successfully created.') % data['name']
            messages.success(request, message)
            return router
        except Exception as exc:
            if exc.status_code == 409:
                msg = _('Quota exceeded for resource router.')
            else:
                msg = _('Failed to create router "%s".') % data['name']
            LOG.info(msg)
            redirect = reverse(self.failure_url)
            exceptions.handle(request, msg, redirect=redirect)
            return False


class UpdateForm(forms.SelfHandlingForm):
    name = forms.CharField(label=_("Name"), required=False)
    admin_state = forms.BooleanField(label=_("Admin State"), required=False)
    router_id = forms.CharField(label=_("ID"),
                                widget=forms.HiddenInput())
    mode = forms.ChoiceField(label=_("Router Type"))

    redirect_url = reverse_lazy('horizon:project:routers:index')

    def __init__(self, request, *args, **kwargs):
        super(UpdateForm, self).__init__(request, *args, **kwargs)
        self.dvr_allowed = api.neutron.get_dvr_permission(self.request,
                                                          "update")
        if not self.dvr_allowed:
            del self.fields['mode']
        elif kwargs.get('initial', {}).get('mode') == 'distributed':
            # Neutron supports only changing from centralized to
            # distributed now.
            mode_choices = [('distributed', _('Distributed'))]
            self.fields['mode'].widget = forms.TextInput(attrs={'readonly':
                                                                'readonly'})
            self.fields['mode'].choices = mode_choices
        else:
            mode_choices = [('centralized', _('Centralized')),
                            ('distributed', _('Distributed'))]
            self.fields['mode'].choices = mode_choices

    def handle(self, request, data):
        try:
            params = {'admin_state_up': data['admin_state'],
                      'name': data['name']}
            if self.dvr_allowed:
                params['distributed'] = (data['mode'] == 'distributed')
            router = api.neutron.router_update(request, data['router_id'],
                                               **params)
            msg = _('Router %s was successfully updated.') % data['name']
            LOG.debug(msg)
            messages.success(request, msg)
            return router
        except Exception:
            msg = _('Failed to update router %s') % data['name']
            LOG.info(msg)
            exceptions.handle(request, msg, redirect=self.redirect_url)
