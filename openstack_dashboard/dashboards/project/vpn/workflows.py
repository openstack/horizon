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

from django.utils.translation import ugettext_lazy as _  # noqa

from horizon import exceptions
from horizon import forms
from horizon.utils import fields
from horizon import workflows

from openstack_dashboard import api


LOG = logging.getLogger(__name__)


class AddVPNServiceAction(workflows.Action):
    name = forms.CharField(max_length=80, label=_("Name"))
    description = forms.CharField(
        initial="", required=False,
        max_length=80, label=_("Description"))
    router_id = forms.ChoiceField(label=_("Router"))
    subnet_id = forms.ChoiceField(label=_("Subnet"))
    admin_state_up = forms.BooleanField(label=_("Admin State"),
                                        initial=True, required=False)

    def __init__(self, request, *args, **kwargs):
        super(AddVPNServiceAction, self).__init__(request, *args, **kwargs)

    def populate_subnet_id_choices(self, request, context):
        subnet_id_choices = [('', _("Select a Subnet"))]
        try:
            tenant_id = request.user.tenant_id
            networks = api.neutron.network_list_for_tenant(request, tenant_id)
        except Exception:
            exceptions.handle(request,
                              _('Unable to retrieve networks list.'))
            networks = []
        for n in networks:
            for s in n['subnets']:
                subnet_id_choices.append((s.id, s.cidr))
        self.fields['subnet_id'].choices = subnet_id_choices
        return subnet_id_choices

    def populate_router_id_choices(self, request, context):
        router_id_choices = [('', _("Select a Router"))]
        try:
            routers = api.neutron.router_list(request)
        except Exception:
            exceptions.handle(request,
                              _('Unable to retrieve routers list.'))
            routers = []
        for r in routers:
            router_id_choices.append((r.id, r.name))
        self.fields['router_id'].choices = router_id_choices
        return router_id_choices

    class Meta:
        name = _("Add New VPNService")
        permissions = ('openstack.services.network',)
        help_text = _("Create VPNService for current tenant.\n\n"
                      "Assign a name and description for the VPNService. "
                      "Select a router and a subnet. "
                      "Admin State is Up (checked) by default."
                      )


class AddVPNServiceStep(workflows.Step):
    action_class = AddVPNServiceAction
    contributes = ("name", "description", "subnet_id",
                   "router_id", "admin_state_up")

    def contribute(self, data, context):
        context = super(AddVPNServiceStep, self).contribute(data, context)
        if data:
            return context


class AddVPNService(workflows.Workflow):
    slug = "addvpnservice"
    name = _("Add VPNService")
    finalize_button_name = _("Add")
    success_message = _('Added VPNService "%s".')
    failure_message = _('Unable to add VPNService "%s".')
    success_url = "horizon:project:vpn:index"
    default_steps = (AddVPNServiceStep,)

    def format_status_message(self, message):
        return message % self.context.get('name')

    def handle(self, request, context):
        try:
            api.vpn.vpnservice_create(request, **context)
            return True
        except Exception:
            return False


class AddIKEPolicyAction(workflows.Action):
    name = forms.CharField(max_length=80, label=_("Name"))
    description = forms.CharField(
        initial="", required=False,
        max_length=80, label=_("Description"))
    auth_algorithm = forms.ChoiceField(label=_("Authorization algorithm"))
    encryption_algorithm = forms.ChoiceField(label=_("Encryption algorithm"))
    ike_version = forms.ChoiceField(label=_("IKE version"))
    lifetime_units = forms.ChoiceField(label=_("Lifetime units for IKE keys"))
    lifetime_value = forms.IntegerField(
        min_value=60, label=_("Lifetime value for IKE keys"),
        initial=3600,
        help_text=_("Equal to or more than 60"))
    pfs = forms.ChoiceField(label=_("Perfect Forward Secrecy"))
    phase1_negotiation_mode = forms.ChoiceField(
        label=_("IKE Phase1 negotiation mode"))

    def __init__(self, request, *args, **kwargs):
        super(AddIKEPolicyAction, self).__init__(request, *args, **kwargs)

        auth_algorithm_choices = [("sha1", "sha1")]
        self.fields['auth_algorithm'].choices = auth_algorithm_choices

        encryption_algorithm_choices = [("3des", "3des"),
                                        ("aes-128", "aes-128"),
                                        ("aes-192", "aes-192"),
                                        ("aes-256", "aes-256")]
        self.fields[
            'encryption_algorithm'].choices = encryption_algorithm_choices

        ike_version_choices = [("v1", "v1"),
                               ("v2", "v2")]
        self.fields['ike_version'].choices = ike_version_choices

        lifetime_units_choices = [("seconds", "seconds")]
        self.fields['lifetime_units'].choices = lifetime_units_choices

        pfs_choices = [("group2", "group2"),
                       ("group5", "group5"),
                       ("group14", "group14")]
        self.fields['pfs'].choices = pfs_choices

        phase1_neg_mode_choices = [("main", "main")]
        self.fields[
            'phase1_negotiation_mode'].choices = phase1_neg_mode_choices

    class Meta:
        name = _("Add New IKEPolicy")
        permissions = ('openstack.services.network',)
        help_text = _("Create IKEPolicy for current tenant.\n\n"
                      "Assign a name and description for the IKEPolicy. "
                      )


class AddIKEPolicyStep(workflows.Step):
    action_class = AddIKEPolicyAction
    contributes = ("name", "description", "auth_algorithm",
                   "encryption_algorithm", "ike_version",
                   "lifetime_units", "lifetime_value",
                   "pfs", "phase1_negotiation_mode")

    def contribute(self, data, context):
        context = super(AddIKEPolicyStep, self).contribute(data, context)
        context.update({'lifetime': {'units': data['lifetime_units'],
                                     'value': data['lifetime_value']}})
        context.pop('lifetime_units')
        context.pop('lifetime_value')
        if data:
            return context


class AddIKEPolicy(workflows.Workflow):
    slug = "addikepolicy"
    name = _("Add IKEPolicy")
    finalize_button_name = _("Add")
    success_message = _('Added IKEPolicy "%s".')
    failure_message = _('Unable to add IKEPolicy "%s".')
    success_url = "horizon:project:vpn:index"
    default_steps = (AddIKEPolicyStep,)

    def format_status_message(self, message):
        return message % self.context.get('name')

    def handle(self, request, context):
        try:
            api.vpn.ikepolicy_create(request, **context)
            return True
        except Exception:
            return False


class AddIPSecPolicyAction(workflows.Action):
    name = forms.CharField(max_length=80, label=_("Name"))
    description = forms.CharField(
        initial="", required=False,
        max_length=80, label=_("Description"))
    auth_algorithm = forms.ChoiceField(label=_("Authorization algorithm"))
    encapsulation_mode = forms.ChoiceField(label=_("Encapsulation mode"))
    encryption_algorithm = forms.ChoiceField(label=_("Encryption algorithm"))
    lifetime_units = forms.ChoiceField(label=_("Lifetime units"))
    lifetime_value = forms.IntegerField(
        min_value=60, label=_("Lifetime value for IKE keys "),
        initial=3600,
        help_text=_("Equal to or more than 60"))
    pfs = forms.ChoiceField(label=_("Perfect Forward Secrecy"))
    transform_protocol = forms.ChoiceField(label=_("Transform Protocol"))

    def __init__(self, request, *args, **kwargs):
        super(AddIPSecPolicyAction, self).__init__(request, *args, **kwargs)

        auth_algorithm_choices = [("sha1", "sha1")]
        self.fields['auth_algorithm'].choices = auth_algorithm_choices

        encapsulation_mode_choices = [("tunnel", "tunnel"),
                                      ("transport", "transport")]
        self.fields['encapsulation_mode'].choices = encapsulation_mode_choices

        encryption_algorithm_choices = [("3des", "3des"),
                                        ("aes-128", "aes-128"),
                                        ("aes-192", "aes-192"),
                                        ("aes-256", "aes-256")]
        self.fields[
            'encryption_algorithm'].choices = encryption_algorithm_choices

        lifetime_units_choices = [("seconds", "seconds")]
        self.fields['lifetime_units'].choices = lifetime_units_choices

        pfs_choices = [("group2", "group2"),
                       ("group5", "group5"),
                       ("group14", "group14")]
        self.fields['pfs'].choices = pfs_choices

        transform_protocol_choices = [("esp", "esp"),
                                      ("ah", "ah"),
                                      ("ah-esp", "ah-esp")]
        self.fields['transform_protocol'].choices = transform_protocol_choices

    class Meta:
        name = _("Add New IPSecPolicy")
        permissions = ('openstack.services.network',)
        help_text = _("Create IPSecPolicy for current tenant.\n\n"
                      "Assign a name and description for the IPSecPolicy. "
                      )


class AddIPSecPolicyStep(workflows.Step):
    action_class = AddIPSecPolicyAction
    contributes = ("name", "description", "auth_algorithm",
                   "encapsulation_mode", "encryption_algorithm",
                   "lifetime_units", "lifetime_value",
                   "pfs", "transform_protocol")

    def contribute(self, data, context):
        context = super(AddIPSecPolicyStep, self).contribute(data, context)
        context.update({'lifetime': {'units': data['lifetime_units'],
                                     'value': data['lifetime_value']}})
        context.pop('lifetime_units')
        context.pop('lifetime_value')
        if data:
            return context


class AddIPSecPolicy(workflows.Workflow):
    slug = "addipsecpolicy"
    name = _("Add IPSecPolicy")
    finalize_button_name = _("Add")
    success_message = _('Added IPSecPolicy "%s".')
    failure_message = _('Unable to add IPSecPolicy "%s".')
    success_url = "horizon:project:vpn:index"
    default_steps = (AddIPSecPolicyStep,)

    def format_status_message(self, message):
        return message % self.context.get('name')

    def handle(self, request, context):
        try:
            api.vpn.ipsecpolicy_create(request, **context)
            return True
        except Exception:
            return False


class AddIPSecSiteConnectionAction(workflows.Action):
    name = forms.CharField(max_length=80, label=_("Name"))
    description = forms.CharField(
        initial="", required=False,
        max_length=80, label=_("Description"))
    dpd_action = forms.ChoiceField(label=_("Dead peer detection actions"))
    dpd_interval = forms.IntegerField(
        min_value=1, label=_("Dead peer detection interval"),
        initial=30,
        help_text=_("valid integer"))
    dpd_timeout = forms.IntegerField(
        min_value=1, label=_("Dead peer detection timeout"),
        initial=120,
        help_text=_("valid integer greater than the dpd-interval"))
    ikepolicy_id = forms.ChoiceField(
        label=_("IKEPolicy associated with this connection"))
    initiator = forms.ChoiceField(label=_("Initiator state"))
    ipsecpolicy_id = forms.ChoiceField(
        label=_("IPsecPolicy associated with this connection"))
    mtu = forms.IntegerField(
        min_value=68,
        label=_("Maximum Transmission Unit size for the connection"),
        initial=1500,
        help_text=_("Equal to or more than 68 if the local subnet is IPv4. "
                    "Equal to or more than 1280 if the local subnet is IPv6."))
    peer_address = fields.IPField(label=_("Remote peer IP Address"),
                                  initial="172.0.0.2",
                                  help_text=_("Remote peer IP Address for "
                                              "the VPN Connection "
                                              "(e.g. 172.0.0.2)"),
                                  version=fields.IPv4 | fields.IPv6,
                                  mask=False)
    peer_cidrs = fields.IPField(label=_("Remote peer subnet"),
                                initial="20.1.0.0/24",
                                help_text=_("Remote peer subnet address "
                                            "with mask in CIDR format "
                                            "(e.g. 20.1.0.0/24)"),
                                version=fields.IPv4 | fields.IPv6,
                                mask=True)
    peer_id = fields.IPField(label=_("Remote branch router identity"),
                             initial="172.0.0.2",
                             help_text=_("IP address of remote branch router "
                                         "(e.g. 172.0.0.2)"),
                             version=fields.IPv4 | fields.IPv6,
                             mask=False)
    psk = forms.CharField(max_length=80, label=_("Pre-Shared Key string"),
                          initial="secret")
    vpnservice_id = forms.ChoiceField(
        label=_("VPNService instance id associated with this connection"))
    admin_state_up = forms.BooleanField(label=_("Admin State"),
                                        initial=True, required=False)

    def __init__(self, request, *args, **kwargs):
        super(AddIPSecSiteConnectionAction, self).__init__(
            request, *args, **kwargs)

        initiator_choices = [("bi-directional", "bi-directional"),
                             ("response-only", "response-only")]
        self.fields['initiator'].choices = initiator_choices

    def populate_dpd_action_choices(self, request, context):
        dpd_action_choices = [("hold", "hold"),
                              ("clear", "clear"),
                              ("disabled", "disabled"),
                              ("restart", "restart"),
                              ("restart-by-peer", "restart-by-peer")]
        self.fields['dpd_action'].choices = dpd_action_choices
        return dpd_action_choices

    def populate_ikepolicy_id_choices(self, request, context):
        ikepolicy_id_choices = [('', _("Select IKEPolicy"))]
        try:
            ikepolicies = api.vpn.ikepolicies_get(request)
        except Exception:
            exceptions.handle(request,
                              _('Unable to retrieve IKEPolicies list.'))
            ikepolicies = []
        for p in ikepolicies:
            ikepolicy_id_choices.append((p.id, p.name))
        self.fields['ikepolicy_id'].choices = ikepolicy_id_choices
        return ikepolicy_id_choices

    def populate_ipsecpolicy_id_choices(self, request, context):
        ipsecpolicy_id_choices = [('', _("Select IPSecPolicy"))]
        try:
            ipsecpolicies = api.vpn.ipsecpolicies_get(request)
        except Exception:
            exceptions.handle(request,
                              _('Unable to retrieve IPSecPolicies list.'))
            ipsecpolicies = []
        for p in ipsecpolicies:
            ipsecpolicy_id_choices.append((p.id, p.name))
        self.fields['ipsecpolicy_id'].choices = ipsecpolicy_id_choices
        return ipsecpolicy_id_choices

    def populate_vpnservice_id_choices(self, request, context):
        vpnservice_id_choices = [('', _("Select VPNService"))]
        try:
            vpnservices = api.vpn.vpnservices_get(request)
        except Exception:
            exceptions.handle(request,
                              _('Unable to retrieve VPNServices list.'))
            vpnservices = []
        for s in vpnservices:
            vpnservice_id_choices.append((s.id, s.name))
        self.fields['vpnservice_id'].choices = vpnservice_id_choices
        return vpnservice_id_choices

    class Meta:
        name = _("Add New IPSecSiteConnection")
        permissions = ('openstack.services.network',)
        help_text = _("Create IPSecSiteConnection for current tenant.\n\n"
                      "Assign a name and description for the "
                      "IPSecSiteConnection. "
                      "Admin State is Up (checked) by default."
                      )


class AddIPSecSiteConnectionStep(workflows.Step):
    action_class = AddIPSecSiteConnectionAction
    contributes = ("name", "description",
                   "dpd_action", "dpd_interval", "dpd_timeout",
                   "ikepolicy_id",
                   "initiator", "ipsecpolicy_id", "mtu", "peer_address",
                   "peer_cidrs", "peer_id", "psk",
                   "vpnservice_id", "admin_state_up")

    def contribute(self, data, context):
        context = super(
            AddIPSecSiteConnectionStep, self).contribute(data, context)
        context.update({'dpd': {'action': data['dpd_action'],
                                'interval': data['dpd_interval'],
                                'timeout': data['dpd_timeout']}})
        context.pop('dpd_action')
        context.pop('dpd_interval')
        context.pop('dpd_timeout')
        if data:
            return context


class AddIPSecSiteConnection(workflows.Workflow):
    slug = "addipsecsiteconnection"
    name = _("Add IPSecSiteConnection")
    finalize_button_name = _("Add")
    success_message = _('Added IPSecSiteConnection "%s".')
    failure_message = _('Unable to add IPSecSiteConnection "%s".')
    success_url = "horizon:project:vpn:index"
    default_steps = (AddIPSecSiteConnectionStep,)

    def format_status_message(self, message):
        return message % self.context.get('name')

    def handle(self, request, context):
        try:
            api.vpn.ipsecsiteconnection_create(request, **context)
            return True
        except Exception:
            return False
