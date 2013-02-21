# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright 2012,  Nachi Ueno,  NTT MCL,  Inc.
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

"""
Views for managing Quantum Routers.
"""
import logging

from django.core.urlresolvers import reverse
from django.utils.translation import ugettext_lazy as _

from horizon import forms
from horizon import exceptions
from horizon import messages
from openstack_dashboard import api

LOG = logging.getLogger(__name__)


class CreateForm(forms.SelfHandlingForm):
    name = forms.CharField(max_length="255",
                           label=_("Router Name"),
                           required=False)
    tenant_id = forms.ChoiceField(label=_("Project"))
    failure_url = 'horizon:admin:routers:index'

    def __init__(self, request, *args, **kwargs):
        super(CreateForm, self).__init__(request, *args, **kwargs)
        tenant_choices = [('', _("Select a project"))]
        try:
            for tenant in api.keystone.tenant_list(request, admin=True):
                if tenant.enabled:
                    tenant_choices.append((tenant.id, tenant.name))
        except:
            msg = _('Failed to get tenants.')
            LOG.warn(msg)
            redirect = reverse(self.failure_url)
            exceptions.handle(request, msg, redirect=redirect)
            return

        self.fields['tenant_id'].choices = tenant_choices

    def handle(self, request, data):
        try:
            params = {}
            if data.get('tenant_id'):
                params['tenant_id'] = data['tenant_id']
            router = api.quantum.router_create(request,
                                               name=data['name'], **params)
            message = 'Creating router "%s"' % data['name']
            messages.info(request, message)
            return router
        except:
            msg = _('Failed to create router "%s".') % data['name']
            LOG.warn(msg)
            redirect = reverse(self.failure_url)
            exceptions.handle(request, msg, redirect=redirect)
            return False
