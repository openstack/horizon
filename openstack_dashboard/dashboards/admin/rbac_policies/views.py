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

from collections import OrderedDict

from django.urls import reverse
from django.urls import reverse_lazy
from django.utils.translation import ugettext_lazy as _

from horizon import exceptions
from horizon import forms
from horizon import messages
from horizon import tables
from horizon import tabs
from horizon.utils import memoized

from openstack_dashboard import api
from openstack_dashboard.dashboards.admin.rbac_policies \
    import forms as rbac_policy_forms
from openstack_dashboard.dashboards.admin.rbac_policies \
    import tables as rbac_policy_tables
from openstack_dashboard.dashboards.admin.rbac_policies \
    import tabs as rbac_policy_tabs


class IndexView(tables.DataTableView):
    table_class = rbac_policy_tables.RBACPoliciesTable
    page_title = _("RBAC Policies")

    @memoized.memoized_method
    def _get_tenants(self):
        try:
            tenants, has_more = api.keystone.tenant_list(self.request)
        except Exception:
            tenants = []
            msg = _("Unable to retrieve information about the "
                    "policies' projects.")
            exceptions.handle(self.request, msg)

        tenant_dict = OrderedDict([(t.id, t.name) for t in tenants])
        return tenant_dict

    def _get_networks(self):
        try:
            networks = api.neutron.network_list(self.request)
        except Exception:
            networks = []
            msg = _("Unable to retrieve information about the "
                    "policies' networks.")
            exceptions.handle(self.request, msg)
        return dict((n.id, n.name) for n in networks)

    def _get_qos_policies(self):
        qos_policies = []
        try:
            if api.neutron.is_extension_supported(self.request,
                                                  extension_alias='qos'):
                qos_policies = api.neutron.policy_list(self.request)
        except Exception:
            msg = _("Unable to retrieve information about the "
                    "policies' qos policies.")
            exceptions.handle(self.request, msg)
        return dict((q.id, q.name) for q in qos_policies)

    def get_data(self):
        try:
            rbac_policies = api.neutron.rbac_policy_list(self.request)
        except Exception:
            rbac_policies = []
            messages.error(self.request,
                           _("Unable to retrieve RBAC policies."))
        if rbac_policies:
            tenant_dict = self._get_tenants()
            network_dict = self._get_networks()
            qos_policy_dict = self._get_qos_policies()
            for p in rbac_policies:
                # Set tenant name and object name
                p.tenant_name = tenant_dict.get(p.tenant_id, p.tenant_id)
                p.target_tenant_name = tenant_dict.get(p.target_tenant,
                                                       p.target_tenant)
                if p.object_type == "network":
                    p.object_name = network_dict.get(p.object_id, p.object_id)
                elif p.object_type == "qos_policy":
                    p.object_name = qos_policy_dict.get(p.object_id,
                                                        p.object_id)
        return rbac_policies


class CreateView(forms.ModalFormView):
    template_name = 'admin/rbac_policies/create.html'
    form_id = "create_rbac_policy_form"
    form_class = rbac_policy_forms.CreatePolicyForm
    submit_label = _("Create RBAC Policy")
    submit_url = reverse_lazy("horizon:admin:rbac_policies:create")
    success_url = reverse_lazy("horizon:admin:rbac_policies:index")
    page_title = _("Create A RBAC Policy")


class UpdateView(forms.ModalFormView):
    context_object_name = 'rbac_policies'
    template_name = 'admin/rbac_policies/update.html'
    form_class = rbac_policy_forms.UpdatePolicyForm
    form_id = "update_rbac_policy_form"
    submit_label = _("Save Changes")
    submit_url = 'horizon:admin:rbac_policies:update'
    success_url = reverse_lazy('horizon:admin:rbac_policies:index')
    page_title = _("Update RBAC Policy")

    def get_context_data(self, **kwargs):
        context = super(UpdateView, self).get_context_data(**kwargs)
        args = (self.kwargs['rbac_policy_id'],)
        context["rbac_policy_id"] = self.kwargs['rbac_policy_id']
        context["submit_url"] = reverse(self.submit_url, args=args)
        return context

    @memoized.memoized_method
    def _get_object(self, *args, **kwargs):
        rbac_policy_id = self.kwargs['rbac_policy_id']
        try:
            return api.neutron.rbac_policy_get(self.request, rbac_policy_id)
        except Exception:
            redirect = self.success_url
            msg = _('Unable to retrieve rbac policy details.')
            exceptions.handle(self.request, msg, redirect=redirect)

    def get_initial(self):
        rbac_policy = self._get_object()
        return {'rbac_policy_id': rbac_policy['id'],
                'target_tenant': rbac_policy['target_tenant']}


class DetailView(tabs.TabView):
    tab_group_class = rbac_policy_tabs.RBACDetailsTabs
    template_name = 'horizon/common/_detail.html'
    page_title = "{{ rbac_policy.id }}"
