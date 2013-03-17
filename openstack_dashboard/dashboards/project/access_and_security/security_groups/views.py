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

"""
Views for managing instances.
"""
import logging

from django.core.urlresolvers import reverse_lazy, reverse
from django.utils.translation import ugettext_lazy as _

from horizon import exceptions
from horizon import forms
from horizon import tables

from openstack_dashboard import api
from ..floating_ips.utils import get_int_or_uuid
from .forms import CreateGroup, AddRule
from .tables import RulesTable


LOG = logging.getLogger(__name__)


class DetailView(tables.DataTableView):
    table_class = RulesTable
    template_name = 'project/access_and_security/security_groups/detail.html'

    def get_data(self):
        security_group_id = get_int_or_uuid(self.kwargs['security_group_id'])
        try:
            self.object = api.nova.security_group_get(self.request,
                                                      security_group_id)
            rules = [api.nova.SecurityGroupRule(rule) for
                     rule in self.object.rules]
        except:
            redirect = reverse('horizon:project:access_and_security:index')
            exceptions.handle(self.request,
                              _('Unable to retrieve security group.'),
                              redirect=redirect)
        return rules


class AddRuleView(forms.ModalFormView):
    form_class = AddRule
    template_name = 'project/access_and_security/security_groups/add_rule.html'

    def get_success_url(self):
        sg_id = self.kwargs['security_group_id']
        return reverse("horizon:project:access_and_security:"
                       "security_groups:detail", args=[sg_id])

    def get_context_data(self, **kwargs):
        context = super(AddRuleView, self).get_context_data(**kwargs)
        context["security_group_id"] = self.kwargs['security_group_id']
        return context

    def get_initial(self):
        return {'id': self.kwargs['security_group_id']}

    def get_form_kwargs(self):
        kwargs = super(AddRuleView, self).get_form_kwargs()

        try:
            groups = api.nova.security_group_list(self.request)
        except:
            groups = []
            exceptions.handle(self.request,
                              _("Unable to retrieve security groups."))

        security_groups = []
        for group in groups:
            if group.id == get_int_or_uuid(self.kwargs['security_group_id']):
                security_groups.append((group.id,
                                        _("%s (current)") % group.name))
            else:
                security_groups.append((group.id, group.name))
        kwargs['sg_list'] = security_groups
        return kwargs


class CreateView(forms.ModalFormView):
    form_class = CreateGroup
    template_name = 'project/access_and_security/security_groups/create.html'
    success_url = reverse_lazy('horizon:project:access_and_security:index')
