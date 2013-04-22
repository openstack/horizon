# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright 2013, Mirantis Inc
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
#
# @author: Tatiana Mazur

import logging

from django.core.urlresolvers import reverse
from django.utils.translation import ugettext_lazy as _

from horizon import exceptions
from horizon import forms
from horizon import messages

from openstack_dashboard import api


LOG = logging.getLogger(__name__)


class UpdatePool(forms.SelfHandlingForm):
    name = forms.CharField(max_length=80, label=_("Name"))
    pool_id = forms.CharField(label=_("ID"),
                                 widget=forms.TextInput(
                                     attrs={'readonly': 'readonly'}))
    description = forms.CharField(required=False,
                                  max_length=80, label=_("Description"))
    lb_method = forms.ChoiceField(label=_("Load Balancing Method"))
    admin_state_up = forms.BooleanField(label=_("Admin State"), required=False)

    failure_url = 'horizon:project:loadbalancers:index'

    def __init__(self, request, *args, **kwargs):
        super(UpdatePool, self).__init__(request, *args, **kwargs)

        lb_method_choices = [('ROUND_ROBIN', 'ROUND_ROBIN'),
                             ('LEAST_CONNECTIONS', 'LEAST_CONNECTIONS'),
                             ('SOURCE_IP', 'SOURCE_IP')]
        self.fields['lb_method'].choices = lb_method_choices

    def handle(self, request, context):
        try:
            data = {'pool': {'name': context['name'],
                             'description': context['description'],
                             'lb_method': context['lb_method'],
                             'admin_state_up': context['admin_state_up'],
                             }}
            pool = api.lbaas.pool_update(request, context['pool_id'], **data)
            msg = _('Pool %s was successfully updated.') % context['name']
            LOG.debug(msg)
            messages.success(request, msg)
            return pool
        except:
            msg = _('Failed to update pool %s') % context['name']
            LOG.info(msg)
            redirect = reverse(self.failure_url)
            exceptions.handle(request, msg, redirect=redirect)
