# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright 2011 United States Government as represented by the
# Administrator of the National Aeronautics and Space Administration.
# All Rights Reserved.
#
# Copyright 2011 Nebula, Inc.
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
Views for managing Nova instances.
"""
import logging

from django.contrib import messages
from django import shortcuts
from django.utils.translation import ugettext as _
from novaclient import exceptions as novaclient_exceptions

from horizon import api
from horizon import forms
from horizon import tables
from .forms import CreateGroup, AddRule
from .tables import RulesTable


LOG = logging.getLogger(__name__)


class EditRulesView(tables.DataTableView):
    table_class = RulesTable
    template_name = 'nova/access_and_security/security_groups/edit_rules.html'

    def get_data(self):
        security_group_id = self.kwargs['security_group_id']
        try:
            self.object = api.security_group_get(self.request,
                                                security_group_id)
            rules = [api.nova.SecurityGroupRule(rule) for
                     rule in self.object.rules]
        except novaclient_exceptions.ClientException, e:
            self.object = None
            rules = []
            LOG.exception("ClientException in security_groups rules edit")
            messages.error(self.request,
                           _('Error getting security_group: %s') % e)
        return rules

    def handle_form(self):
        tenant_id = self.request.user.tenant_id
        initial = {'tenant_id': tenant_id,
                   'security_group_id': self.kwargs['security_group_id']}
        return AddRule.maybe_handle(self.request, initial=initial)

    def get(self, request, *args, **kwargs):
        form, handled = self.handle_form()
        if handled:
            return handled
        tables = self.get_tables()
        if not self.object:
            return shortcuts.redirect("horizon:nova:access_and_security:index")
        context = self.get_context_data(**kwargs)
        context['form'] = form
        context['security_group'] = self.object
        if request.is_ajax():
            context['hide'] = True
            self.template_name = ('nova/access_and_security/security_groups'
                                 '/_edit_rules.html')
        return self.render_to_response(context)

    def post(self, request, *args, **kwargs):
        form, handled = self.handle_form()
        if handled:
            return handled
        return super(EditRulesView, self).post(request, *args, **kwargs)


class CreateView(forms.ModalFormView):
    form_class = CreateGroup
    template_name = 'nova/access_and_security/security_groups/create.html'

    def get_initial(self):
        return {"tenant_id": self.request.user.tenant_id}
