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
from django.urls import reverse
from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _
from neutronclient.common import exceptions as neutron_exc

from horizon import exceptions
from horizon import forms
from horizon import tables
from horizon.utils import memoized

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

        def _sort_key(rule):
            return (
                rule.direction or '',
                rule.ethertype or '',
                # IP protocol can be a string, an integer or None,
                # so we need to normalize into string
                # to make sorting work with py3
                str(rule.ip_protocol) if rule.ip_protocol is not None else '',
                rule.from_port or 0,
                rule.to_port or 0,
            )

        return sorted(data.rules, key=_sort_key)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
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
        context = super().get_context_data(**kwargs)
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
        context = super().get_context_data(**kwargs)
        context["security_group_id"] = self.kwargs['security_group_id']
        args = (self.kwargs['security_group_id'],)
        context['submit_url'] = reverse(self.submit_url, args=args)
        context['cancel_url'] = reverse(self.url, args=args)
        return context

    def get_initial(self):
        return {'id': self.kwargs['security_group_id']}

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()

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


class UpdateRuleView(forms.ModalFormView):
    form_class = project_forms.UpdateRule
    form_id = "update_security_group_rule_form"
    modal_id = "update_security_group_rule_modal"
    template_name = 'project/security_groups/update_rule.html'
    submit_label = _("Save")
    submit_url = "horizon:project:security_groups:update_rule"
    url = "horizon:project:security_groups:detail"
    page_title = _("Edit Rule")

    def get_success_url(self):
        sg_id = self.kwargs['security_group_id']
        return reverse(self.url, args=[sg_id])

    @memoized.memoized_method
    def get_security_group(self):
        sg_id = filters.get_int_or_uuid(self.kwargs['security_group_id'])
        try:
            return api.neutron.security_group_get(self.request, sg_id)
        except Exception:
            redirect = reverse('horizon:project:security_groups:index')
            exceptions.handle(self.request,
                              _('Unable to retrieve security group.'),
                              redirect=redirect)

    @memoized.memoized_method
    def get_rule(self):
        security_group = self.get_security_group()
        if security_group is None:
            return None
        rule_id = filters.get_int_or_uuid(self.kwargs['rule_id'])
        for rule in security_group.rules:
            if filters.get_int_or_uuid(rule.id) == rule_id:
                return rule
        redirect = reverse(self.url, args=[self.kwargs['security_group_id']])
        exceptions.handle(self.request,
                          _('Unable to retrieve security group rule.'),
                          redirect=redirect)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["security_group"] = self.get_security_group()
        context["rule"] = self.get_rule()
        sg_args = (self.kwargs['security_group_id'],)
        context['cancel_url'] = reverse(self.url, args=sg_args)
        context['security_group_id'] = self.kwargs['security_group_id']
        submit_args = (self.kwargs['security_group_id'],
                       self.kwargs['rule_id'])
        context['submit_url'] = reverse(self.submit_url, args=submit_args)
        return context

    def _get_rule_menu_initial(self, rule):
        proto = rule.ip_protocol
        if proto is None:
            return 'custom'
        if isinstance(proto, str):
            proto_value = proto.lower()
        else:
            proto_value = str(proto)
        if proto_value in ('tcp', '6'):
            return 'tcp'
        if proto_value in ('udp', '17'):
            return 'udp'
        if proto_value in ('icmp', 'ipv6-icmp', '1', '58'):
            return 'icmp'
        return 'custom'

    def _get_remote_initial(self, rule):
        remote = 'cidr'
        cidr = rule.ip_range.get('cidr')
        security_group = None
        if getattr(rule, 'remote_group_id', None):
            remote = 'sg'
            security_group = rule.remote_group_id
        return remote, cidr, security_group

    def _get_port_initials(self, rule):
        from_port = rule.from_port
        to_port = rule.to_port
        port = None
        port_or_range = 'all'
        if from_port is None and to_port is None:
            port_or_range = 'all'
        elif from_port == to_port:
            port_or_range = 'port'
            port = from_port
        else:
            port_or_range = 'range'
        return port_or_range, port, from_port, to_port

    def get_initial(self):
        rule = self.get_rule()
        initial = {'id': self.kwargs['security_group_id'],
                   'rule_id': self.kwargs['rule_id']}
        if not rule:
            return initial
        remote, cidr, security_group = self._get_remote_initial(rule)
        port_or_range, port, from_port, to_port = self._get_port_initials(rule)
        initial.update({
            'direction': rule.direction or 'ingress',
            'ethertype': rule.ethertype or 'IPv4',
            'ip_protocol': rule.ip_protocol,
            'rule_menu': self._get_rule_menu_initial(rule),
            'port_or_range': port_or_range,
            'port': port,
            'from_port': from_port,
            'to_port': to_port,
            'icmp_type': rule.from_port,
            'icmp_code': rule.to_port,
            'remote': remote,
            'cidr': cidr,
            'security_group': security_group,
            'description': rule.description,
        })
        return initial

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()

        try:
            groups = api.neutron.security_group_list(self.request)
        except Exception:
            groups = []
            exceptions.handle(self.request,
                              _("Unable to retrieve security groups."))

        security_groups = []
        current_id = filters.get_int_or_uuid(
            self.kwargs['security_group_id'])
        for group in groups:
            if group.id == current_id:
                security_groups.append((group.id,
                                        _("%s (current)") % group.name))
            else:
                security_groups.append((group.id, group.name))
        kwargs['sg_list'] = security_groups
        kwargs['current_rule'] = self.get_rule()
        return kwargs


class CreateView(forms.ModalFormView):
    form_class = project_forms.CreateGroup
    form_id = "create_security_group_form"
    modal_id = "create_security_group_modal"
    template_name = 'project/security_groups/create.html'
    cancel_url = "horizon:project:security_groups:create"
    submit_label = _("Create Security Group")
    submit_url = reverse_lazy(
        "horizon:project:security_groups:create")
    page_title = _("Create Security Group")

    def get_success_url_from_handled(self, handled):
        return reverse('horizon:project:security_groups:detail',
                       args=[handled.id])


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
