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
from django.core.urlresolvers import reverse
from django.core.urlresolvers import reverse_lazy
from django.utils.translation import ugettext_lazy as _

from horizon import exceptions
from horizon import forms
from horizon import tables
from horizon.utils import memoized

from neutronclient.common import exceptions as neutron_exc

from openstack_dashboard import api
from openstack_dashboard.dashboards.project.security_groups \
    import forms as project_forms
from openstack_dashboard.dashboards.project.security_groups \
    import tables as project_tables
from openstack_dashboard.utils import filters


class DetailView(tables.DataTableView):
    table_class = project_tables.RulesTable
    template_name = 'project/security_groups/detail.html'
    page_title = _("Manage Security Group Rules: "
                   "{{ security_group.name }} ({{ security_group.id }})")

    @memoized.memoized_method
    def _get_data(self):
        sg_id = filters.get_int_or_uuid(self.kwargs['security_group_id'])
        try:
            return api.neutron.security_group_get(self.request, sg_id)
        except Exception:
            redirect = reverse('horizon:project:security_groups:index')
            exceptions.handle(self.request,
                              _('Unable to retrieve security group.'),
                              redirect=redirect)

    def get_data(self):
        data = self._get_data()
        if data is None:
            return []
        return sorted(data.rules, key=lambda rule: (rule.ip_protocol or '',
                                                    rule.from_port or 0))

    def get_context_data(self, **kwargs):
        context = super(DetailView, self).get_context_data(**kwargs)
        context["security_group"] = self._get_data()
        return context


class UpdateView(forms.ModalFormView):
    form_class = project_forms.UpdateGroup
    form_id = "update_security_group_form"
    modal_id = "update_security_group_modal"
    template_name = 'project/security_groups/update.html'
    submit_label = _("Edit Security Group")
    submit_url = "horizon:project:security_groups:update"
    success_url = reverse_lazy('horizon:project:security_groups:index')
    page_title = _("Edit Security Group")

    @memoized.memoized_method
    def get_object(self):
        sg_id = filters.get_int_or_uuid(self.kwargs['security_group_id'])
        try:
            return api.neutron.security_group_get(self.request, sg_id)
        except Exception:
            msg = _('Unable to retrieve security group.')
            url = reverse('horizon:project:security_groups:index')
            exceptions.handle(self.request, msg, redirect=url)

    def get_context_data(self, **kwargs):
        context = super(UpdateView, self).get_context_data(**kwargs)
        context["security_group"] = self.get_object()
        args = (self.kwargs['security_group_id'],)
        context['submit_url'] = reverse(self.submit_url, args=args)
        return context

    def get_initial(self):
        security_group = self.get_object()
        return {'id': self.kwargs['security_group_id'],
                'name': security_group.name,
                'description': security_group.description}


class AddRuleView(forms.ModalFormView):
    form_class = project_forms.AddRule
    form_id = "create_security_group_rule_form"
    modal_id = "create_security_group_rule_modal"
    template_name = 'project/security_groups/add_rule.html'
    submit_label = _("Add")
    submit_url = "horizon:project:security_groups:add_rule"
    url = "horizon:project:security_groups:detail"
    page_title = _("Add Rule")

    def get_success_url(self):
        sg_id = self.kwargs['security_group_id']
        return reverse(self.url, args=[sg_id])

    def get_context_data(self, **kwargs):
        context = super(AddRuleView, self).get_context_data(**kwargs)
        context["security_group_id"] = self.kwargs['security_group_id']
        args = (self.kwargs['security_group_id'],)
        context['submit_url'] = reverse(self.submit_url, args=args)
        context['cancel_url'] = reverse(self.url, args=args)
        return context

    def get_initial(self):
        return {'id': self.kwargs['security_group_id']}

    def get_form_kwargs(self):
        kwargs = super(AddRuleView, self).get_form_kwargs()

        try:
            groups = api.neutron.security_group_list(self.request)
        except Exception:
            groups = []
            exceptions.handle(self.request,
                              _("Unable to retrieve security groups."))

        security_groups = []
        for group in groups:
            if group.id == filters.get_int_or_uuid(
                    self.kwargs['security_group_id']):
                security_groups.append((group.id,
                                        _("%s (current)") % group.name))
            else:
                security_groups.append((group.id, group.name))
        kwargs['sg_list'] = security_groups
        return kwargs


class CreateView(forms.ModalFormView):
    form_class = project_forms.CreateGroup
    form_id = "create_security_group_form"
    modal_id = "create_security_group_modal"
    template_name = 'project/security_groups/create.html'
    submit_label = _("Create Security Group")
    submit_url = reverse_lazy(
        "horizon:project:security_groups:create")
    success_url = reverse_lazy('horizon:project:security_groups:index')
    page_title = _("Create Security Group")


class IndexView(tables.DataTableView):
    table_class = project_tables.SecurityGroupsTable
    page_title = _("Security Groups")

    def get_data(self):
        try:
            security_groups = api.neutron.security_group_list(self.request)
        except neutron_exc.ConnectionFailed:
            security_groups = []
            exceptions.handle(self.request)
        except Exception:
            security_groups = []
            exceptions.handle(self.request,
                              _('Unable to retrieve security groups.'))
        return sorted(security_groups, key=lambda group: group.name)
