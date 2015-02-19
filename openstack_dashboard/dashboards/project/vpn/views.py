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

from django.core.urlresolvers import reverse
from django.core.urlresolvers import reverse_lazy
from django.utils.translation import ugettext_lazy as _

from horizon import exceptions
from horizon import forms
from horizon import messages
from horizon import tabs
from horizon.utils import memoized
from horizon import workflows

from openstack_dashboard import api

from openstack_dashboard.dashboards.project.vpn \
    import forms as vpn_forms
from openstack_dashboard.dashboards.project.vpn import tables as vpn_tables
from openstack_dashboard.dashboards.project.vpn import tabs as vpn_tabs
from openstack_dashboard.dashboards.project.vpn \
    import workflows as vpn_workflows

import re


class IndexView(tabs.TabView):
    tab_group_class = vpn_tabs.VPNTabs
    template_name = 'project/vpn/index.html'
    page_title = _("Virtual Private Network")

    def post(self, request, *args, **kwargs):
        obj_ids = request.POST.getlist('object_ids')
        action = request.POST['action']
        m = re.search('.delete([a-z]+)', action).group(1)
        if obj_ids == []:
            obj_ids.append(re.search('([0-9a-z-]+)$', action).group(1))
        if m == 'vpnservice':
            for obj_id in obj_ids:
                try:
                    api.vpn.vpnservice_delete(request, obj_id)
                    messages.success(request,
                                     _('Deleted VPN Service %s') % obj_id)
                except Exception as e:
                    exceptions.handle(request,
                                      _('Unable to delete VPN Service: %s')
                                      % e)
        elif m == 'ikepolicy':
            for obj_id in obj_ids:
                try:
                    api.vpn.ikepolicy_delete(request, obj_id)
                    messages.success(request,
                                     _('Deleted IKE Policy %s') % obj_id)
                except Exception as e:
                    exceptions.handle(request,
                                      _('Unable to delete IKE Policy: %s') % e)
        elif m == 'ipsecpolicy':
            for obj_id in obj_ids:
                try:
                    api.vpn.ipsecpolicy_delete(request, obj_id)
                    messages.success(request,
                                     _('Deleted IPSec Policy %s') % obj_id)
                except Exception as e:
                    exceptions.handle(request,
                                      _('Unable to delete IPSec Policy: %s')
                                      % e)
        elif m == 'ipsecsiteconnection':
            for obj_id in obj_ids:
                try:
                    api.vpn.ipsecsiteconnection_delete(request, obj_id)
                    messages.success(request,
                                     _('Deleted IPSec Site Connection %s')
                                     % obj_id)
                except Exception as e:
                    exceptions.handle(
                        request,
                        _('Unable to delete IPSec Site Connection: %s') % e)

        return self.get(request, *args, **kwargs)


class AddVPNServiceView(workflows.WorkflowView):
    workflow_class = vpn_workflows.AddVPNService

    def get_initial(self):
        initial = super(AddVPNServiceView, self).get_initial()
        return initial


class AddIPSecSiteConnectionView(workflows.WorkflowView):
    workflow_class = vpn_workflows.AddIPSecSiteConnection

    def get_initial(self):
        initial = super(AddIPSecSiteConnectionView, self).get_initial()
        return initial


class AddIKEPolicyView(workflows.WorkflowView):
    workflow_class = vpn_workflows.AddIKEPolicy

    def get_initial(self):
        initial = super(AddIKEPolicyView, self).get_initial()
        return initial


class AddIPSecPolicyView(workflows.WorkflowView):
    workflow_class = vpn_workflows.AddIPSecPolicy

    def get_initial(self):
        initial = super(AddIPSecPolicyView, self).get_initial()
        return initial


class IKEPolicyDetailsView(tabs.TabView):
    tab_group_class = vpn_tabs.IKEPolicyDetailsTabs
    template_name = 'project/vpn/details_tabs.html'
    page_title = _("Virtual Private Network")

    @memoized.memoized_method
    def get_data(self):
        pid = self.kwargs['ikepolicy_id']
        try:
            return api.vpn.ikepolicy_get(self.request, pid)
        except Exception:
            msg = _('Unable to retrieve IKE Policy details.')
            exceptions.handle(self.request, msg,
                              redirect=self.get_redirect_url())

    def get_context_data(self, **kwargs):
        context = super(IKEPolicyDetailsView, self).get_context_data(**kwargs)
        ikepolicy = self.get_data()
        table = vpn_tables.IKEPoliciesTable(self.request)
        context["ikepolicy"] = ikepolicy
        context["url"] = self.get_redirect_url()
        context["actions"] = table.render_row_actions(ikepolicy)
        return context

    def get_tabs(self, request, *args, **kwargs):
        ikepolicy = self.get_data()
        return self.tab_group_class(request, ikepolicy=ikepolicy, **kwargs)

    @staticmethod
    def get_redirect_url():
        return reverse_lazy('horizon:project:vpn:index')


class IPSecPolicyDetailsView(tabs.TabView):
    tab_group_class = vpn_tabs.IPSecPolicyDetailsTabs
    template_name = 'project/vpn/details_tabs.html'

    @memoized.memoized_method
    def get_data(self):
        pid = self.kwargs['ipsecpolicy_id']
        try:
            return api.vpn.ipsecpolicy_get(self.request, pid)
        except Exception:
            msg = _('Unable to retrieve IPSec Policy details.')
            exceptions.handle(self.request, msg,
                              redirect=self.get_redirect_url())

    def get_context_data(self, **kwargs):
        context = super(IPSecPolicyDetailsView, self).get_context_data(
            **kwargs)
        ipsecpolicy = self.get_data()
        table = vpn_tables.IPSecPoliciesTable(self.request)
        context["ipsecpolicy"] = ipsecpolicy
        context["url"] = self.get_redirect_url()
        context["actions"] = table.render_row_actions(ipsecpolicy)
        return context

    def get_tabs(self, request, *args, **kwargs):
        ipsecpolicy = self.get_data()
        return self.tab_group_class(request, ipsecpolicy=ipsecpolicy, **kwargs)

    @staticmethod
    def get_redirect_url():
        return reverse_lazy('horizon:project:vpn:index')


class VPNServiceDetailsView(tabs.TabView):
    tab_group_class = vpn_tabs.VPNServiceDetailsTabs
    template_name = 'project/vpn/details_tabs.html'

    @memoized.memoized_method
    def get_data(self):
        sid = self.kwargs['vpnservice_id']

        try:
            vpnservice = api.vpn.vpnservice_get(self.request, sid)
        except Exception:
            vpnservice = []
            msg = _('Unable to retrieve VPN Service details.')
            exceptions.handle(self.request, msg,
                              redirect=self.get_redirect_url())
        try:
            connections = api.vpn.ipsecsiteconnection_list(
                self.request, vpnservice_id=sid)
            vpnservice.vpnconnections = connections
        except Exception:
            vpnservice.vpnconnections = []

        return vpnservice

    def get_context_data(self, **kwargs):
        context = super(VPNServiceDetailsView, self).get_context_data(**kwargs)
        vpnservice = self.get_data()
        table = vpn_tables.VPNServicesTable(self.request)
        context["vpnservice"] = vpnservice
        context["url"] = self.get_redirect_url()
        context["actions"] = table.render_row_actions(vpnservice)
        return context

    def get_tabs(self, request, *args, **kwargs):
        vpnservice = self.get_data()
        return self.tab_group_class(request, vpnservice=vpnservice, **kwargs)

    @staticmethod
    def get_redirect_url():
        return reverse_lazy('horizon:project:vpn:index')


class IPSecSiteConnectionDetailsView(tabs.TabView):
    tab_group_class = vpn_tabs.IPSecSiteConnectionDetailsTabs
    template_name = 'project/vpn/details_tabs.html'

    @memoized.memoized_method
    def get_data(self):
        cid = self.kwargs['ipsecsiteconnection_id']
        try:
            return api.vpn.ipsecsiteconnection_get(self.request, cid)
        except Exception:
            msg = _('Unable to retrieve IPSec Site Connection details.')
            exceptions.handle(self.request, msg,
                              redirect=self.get_redirect_url())

    def get_context_data(self, **kwargs):
        context = super(IPSecSiteConnectionDetailsView, self).get_context_data(
            **kwargs)
        ipsecsiteconnection = self.get_data()
        table = vpn_tables.IPSecSiteConnectionsTable(self.request)
        context["ipsecsiteconnection"] = ipsecsiteconnection
        context["url"] = self.get_redirect_url()
        context["actions"] = table.render_row_actions(ipsecsiteconnection)
        return context

    def get_tabs(self, request, *args, **kwargs):
        ipsecsiteconnection = self.get_data()
        return self.tab_group_class(request,
                                    ipsecsiteconnection=ipsecsiteconnection,
                                    **kwargs)

    @staticmethod
    def get_redirect_url():
        return reverse_lazy('horizon:project:vpn:index')


class UpdateVPNServiceView(forms.ModalFormView):
    form_class = vpn_forms.UpdateVPNService
    form_id = "update_vpnservice_form"
    modal_header = _("Edit VPN Service")
    template_name = "project/vpn/update_vpnservice.html"
    context_object_name = 'vpnservice'
    submit_label = _("Save Changes")
    submit_url = "horizon:project:vpn:update_vpnservice"
    success_url = reverse_lazy("horizon:project:vpn:index")
    page_title = _("Edit VPN Service")

    def get_context_data(self, **kwargs):
        context = super(UpdateVPNServiceView, self).get_context_data(**kwargs)
        context["vpnservice_id"] = self.kwargs['vpnservice_id']
        args = (self.kwargs['vpnservice_id'],)
        context['submit_url'] = reverse(self.submit_url, args=args)
        return context

    @memoized.memoized_method
    def _get_object(self, *args, **kwargs):
        vpnservice_id = self.kwargs['vpnservice_id']
        try:
            return api.vpn.vpnservice_get(self.request, vpnservice_id)
        except Exception as e:
            redirect = self.success_url
            msg = _('Unable to retrieve VPN Service details. %s') % e
            exceptions.handle(self.request, msg, redirect=redirect)

    def get_initial(self):
        vpnservice = self._get_object()
        return {'name': vpnservice['name'],
                'vpnservice_id': vpnservice['id'],
                'description': vpnservice['description'],
                'admin_state_up': vpnservice['admin_state_up']}


class UpdateIKEPolicyView(forms.ModalFormView):
    form_class = vpn_forms.UpdateIKEPolicy
    form_id = "update_ikepolicy_form"
    modal_header = _("Edit IKE Policy")
    template_name = "project/vpn/update_ikepolicy.html"
    context_object_name = 'ikepolicy'
    submit_label = _("Save Changes")
    submit_url = "horizon:project:vpn:update_ikepolicy"
    success_url = reverse_lazy("horizon:project:vpn:index")
    page_title = _("Edit IKE Policy")

    def get_context_data(self, **kwargs):
        context = super(UpdateIKEPolicyView, self).get_context_data(**kwargs)
        context["ikepolicy_id"] = self.kwargs['ikepolicy_id']
        args = (self.kwargs['ikepolicy_id'],)
        context['submit_url'] = reverse(self.submit_url, args=args)
        return context

    @memoized.memoized_method
    def _get_object(self, *args, **kwargs):
        ikepolicy_id = self.kwargs['ikepolicy_id']
        try:
            return api.vpn.ikepolicy_get(self.request, ikepolicy_id)
        except Exception as e:
            redirect = self.success_url
            msg = _('Unable to retrieve IKE Policy details. %s') % e
            exceptions.handle(self.request, msg, redirect=redirect)

    def get_initial(self):
        ikepolicy = self._get_object()
        return {'name': ikepolicy['name'],
                'ikepolicy_id': ikepolicy['id'],
                'description': ikepolicy['description'],
                'auth_algorithm': ikepolicy['auth_algorithm'],
                'encryption_algorithm': ikepolicy['encryption_algorithm'],
                'ike_version': ikepolicy['ike_version'],
                'lifetime_units': ikepolicy['lifetime']['units'],
                'lifetime_value': ikepolicy['lifetime']['value'],
                'pfs': ikepolicy['pfs'],
                'phase1_negotiation_mode': ikepolicy[
                    'phase1_negotiation_mode']}


class UpdateIPSecPolicyView(forms.ModalFormView):
    form_class = vpn_forms.UpdateIPSecPolicy
    form_id = "update_ipsecpolicy_form"
    modal_header = _("Edit IPSec Policy")
    template_name = "project/vpn/update_ipsecpolicy.html"
    context_object_name = 'ipsecpolicy'
    submit_label = _("Save Changes")
    submit_url = "horizon:project:vpn:update_ipsecpolicy"
    success_url = reverse_lazy("horizon:project:vpn:index")
    page_title = _("Edit IPSec Policy")

    def get_context_data(self, **kwargs):
        context = super(UpdateIPSecPolicyView, self).get_context_data(**kwargs)
        context["ipsecpolicy_id"] = self.kwargs['ipsecpolicy_id']
        args = (self.kwargs['ipsecpolicy_id'],)
        context['submit_url'] = reverse(self.submit_url, args=args)
        return context

    @memoized.memoized_method
    def _get_object(self, *args, **kwargs):
        ipsecpolicy_id = self.kwargs['ipsecpolicy_id']
        try:
            return api.vpn.ipsecpolicy_get(self.request, ipsecpolicy_id)
        except Exception as e:
            redirect = self.success_url
            msg = _('Unable to retrieve IPSec Policy details. %s') % e
            exceptions.handle(self.request, msg, redirect=redirect)

    def get_initial(self):
        ipsecpolicy = self._get_object()
        return {'name': ipsecpolicy['name'],
                'ipsecpolicy_id': ipsecpolicy['id'],
                'description': ipsecpolicy['description'],
                'auth_algorithm': ipsecpolicy['auth_algorithm'],
                'encapsulation_mode': ipsecpolicy['encapsulation_mode'],
                'encryption_algorithm': ipsecpolicy['encryption_algorithm'],
                'lifetime_units': ipsecpolicy['lifetime']['units'],
                'lifetime_value': ipsecpolicy['lifetime']['value'],
                'pfs': ipsecpolicy['pfs'],
                'transform_protocol': ipsecpolicy['transform_protocol']}


class UpdateIPSecSiteConnectionView(forms.ModalFormView):
    form_class = vpn_forms.UpdateIPSecSiteConnection
    form_id = "update_ipsecsiteconnection_form"
    modal_header = _("Edit IPSec Site Connection")
    template_name = "project/vpn/update_ipsecsiteconnection.html"
    context_object_name = 'ipsecsiteconnection'
    submit_label = _("Save Changes")
    submit_url = "horizon:project:vpn:update_ipsecsiteconnection"
    success_url = reverse_lazy("horizon:project:vpn:index")
    page_title = _("Edit IPSec Site Connection")

    def get_context_data(self, **kwargs):
        context = super(
            UpdateIPSecSiteConnectionView, self).get_context_data(**kwargs)
        context["ipsecsiteconnection_id"] = self.kwargs[
            'ipsecsiteconnection_id']
        args = (self.kwargs['ipsecsiteconnection_id'],)
        context['submit_url'] = reverse(self.submit_url, args=args)
        return context

    @memoized.memoized_method
    def _get_object(self, *args, **kwargs):
        connection_id = self.kwargs['ipsecsiteconnection_id']
        try:
            return api.vpn.ipsecsiteconnection_get(self.request, connection_id)
        except Exception as e:
            redirect = self.success_url
            msg = _('Unable to retrieve IPSec Site Connection details. %s') % e
            exceptions.handle(self.request, msg, redirect=redirect)

    def get_initial(self):
        ipsecsiteconnection = self._get_object()
        return {'name': ipsecsiteconnection['name'],
                'ipsecsiteconnection_id': ipsecsiteconnection['id'],
                'description': ipsecsiteconnection['description'],
                'peer_address': ipsecsiteconnection['peer_address'],
                'peer_id': ipsecsiteconnection['peer_id'],
                'peer_cidrs': ", ".join(ipsecsiteconnection['peer_cidrs']),
                'psk': ipsecsiteconnection['psk'],
                'mtu': ipsecsiteconnection['mtu'],
                'dpd_action': ipsecsiteconnection['dpd']['action'],
                'dpd_interval': ipsecsiteconnection['dpd']['interval'],
                'dpd_timeout': ipsecsiteconnection['dpd']['timeout'],
                'initiator': ipsecsiteconnection['initiator'],
                'admin_state_up': ipsecsiteconnection['admin_state_up']}
