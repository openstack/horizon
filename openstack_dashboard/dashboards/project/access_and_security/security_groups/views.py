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

from django import shortcuts
from django.core.urlresolvers import reverse_lazy
from django.utils.translation import ugettext_lazy as _

from horizon import exceptions
from horizon import forms
from horizon import tables

from openstack_dashboard import api
from .forms import CreateGroup, AddRule
from .tables import RulesTable


LOG = logging.getLogger(__name__)


class EditRulesView(tables.DataTableView, forms.ModalFormView):
    table_class = RulesTable
    form_class = AddRule
    template_name = ('project/access_and_security/security_groups/'
                     'edit_rules.html')
    success_url = reverse_lazy("horizon:project:access_and_security:index")

    def get_data(self):
        security_group_id = int(self.kwargs['security_group_id'])
        try:
            self.object = api.security_group_get(self.request,
                                                 security_group_id)
            rules = [api.nova.SecurityGroupRule(rule) for
                     rule in self.object.rules]
        except:
            self.object = None
            rules = []
            exceptions.handle(self.request,
                              _('Unable to retrieve security group.'))
        return rules

    def get_initial(self):
        return {'security_group_id': self.kwargs['security_group_id']}

    def get_form_kwargs(self):
        kwargs = super(EditRulesView, self).get_form_kwargs()

        try:
            groups = api.security_group_list(self.request)
        except:
            groups = []
            exceptions.handle(self.request,
                              _("Unable to retrieve security groups."))

        security_groups = []
        for group in groups:
            if group.id == int(self.kwargs['security_group_id']):
                security_groups.append((group.id,
                                        _("%s (current)") % group.name))
            else:
                security_groups.append((group.id, group.name))
        kwargs['sg_list'] = security_groups
        return kwargs

    def get_form(self):
        if not hasattr(self, "_form"):
            form_class = self.get_form_class()
            self._form = super(EditRulesView, self).get_form(form_class)
        return self._form

    def get_context_data(self, **kwargs):
        context = super(EditRulesView, self).get_context_data(**kwargs)
        context['form'] = self.get_form()
        if self.request.is_ajax():
            context['hide'] = True
        return context

    def get(self, request, *args, **kwargs):
        # Table action handling
        handled = self.construct_tables()
        if handled:
            return handled
        if not self.object:  # Set during table construction.
            return shortcuts.redirect(self.success_url)
        context = self.get_context_data(**kwargs)
        context['security_group'] = self.object
        return self.render_to_response(context)

    def post(self, request, *args, **kwargs):
        form = self.get_form()
        if form.is_valid():
            return self.form_valid(form)
        else:
            return self.get(request, *args, **kwargs)


class CreateView(forms.ModalFormView):
    form_class = CreateGroup
    template_name = 'project/access_and_security/security_groups/create.html'
    success_url = reverse_lazy('horizon:project:access_and_security:index')
