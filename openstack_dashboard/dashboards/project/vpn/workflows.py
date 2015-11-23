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

from django.utils.translation import ugettext_lazy as _

from horizon import exceptions
from horizon import forms
from horizon import workflows

from openstack_dashboard import api


class AddVPNServiceAction(workflows.Action):
    name = forms.CharField(max_length=80, label=_("Name"), required=False)
    description = forms.CharField(
        initial="", required=False,
        max_length=80, label=_("Description"))
    router_id = forms.ChoiceField(label=_("Router"))
    subnet_id = forms.ChoiceField(label=_("Subnet"))
    admin_state_up = forms.ChoiceField(
        choices=[(True, _('UP')), (False, _('DOWN'))],
        label=_("Admin State"),
        help_text=_("The state of VPN service to start in. "
                    "If DOWN (False) VPN service does not forward packets."),
        required=False)

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
            tenant_id = request.user.tenant_id
            routers = api.neutron.router_list(request, tenant_id=tenant_id)
        except Exception:
            exceptions.handle(request,
                              _('Unable to retrieve routers list.'))
            routers = []
        for r in routers:
            router_id_choices.append((r.id, r.name))
        self.fields['router_id'].choices = router_id_choices
        return router_id_choices

    class Meta(object):
        name = _("Add New VPN Service")
        permissions = ('openstack.services.network',)
        help_text = _("Create VPN Service for current project.\n\n"
                      "The VPN service is attached to a router "
                      "and references to a single subnet "
                      "to push to a remote site.\n"
                      "Specify a name, description, router, and subnet "
                      "for the VPN Service. "
                      "Admin State is UP (True) by default.\n\n"
                      "The router, subnet and admin state "
                      "fields are required, "
                      "all others are optional."
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
    name = _("Add VPN Service")
    finalize_button_name = _("Add")
    success_message = _('Added VPN Service "%s".')
    failure_message = _('Unable to add VPN Service "%s".')
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
    name = forms.CharField(max_length=80, label=_("Name"), required=False)
    description = forms.CharField(
        initial="", required=False,
        max_length=80, label=_("Description"))
    auth_algorithm = forms.ChoiceField(label=_("Authorization algorithm"),
                                       required=False)
    encryption_algorithm = forms.ChoiceField(label=_("Encryption algorithm"),
                                             required=False)
    ike_version = forms.ChoiceField(label=_("IKE version"), required=False)
    lifetime_units = forms.ChoiceField(label=_("Lifetime units for IKE keys"),
                                       required=False)
    lifetime_value = forms.IntegerField(
        min_value=60, label=_("Lifetime value for IKE keys"),
        initial=3600,
        help_text=_("Equal to or greater than 60"),
        required=False)
    pfs = forms.ChoiceField(label=_("Perfect Forward Secrecy"), required=False)
    phase1_negotiation_mode = forms.ChoiceField(
        label=_("IKE Phase1 negotiation mode"), required=False)

    def __init__(self, request, *args, **kwargs):
        super(AddIKEPolicyAction, self).__init__(request, *args, **kwargs)

        auth_algorithm_choices = [("sha1", "sha1")]
        self.fields['auth_algorithm'].choices = auth_algorithm_choices
        # Currently this field has only one choice, so mark it as readonly.
        self.fields['auth_algorithm'].widget.attrs['readonly'] = True

        encryption_algorithm_choices = [("3des", "3des"),
                                        ("aes-128", "aes-128"),
                                        ("aes-192", "aes-192"),
                                        ("aes-256", "aes-256")]
        self.fields[
            'encryption_algorithm'].choices = encryption_algorithm_choices
        self.fields['encryption_algorithm'].initial = "aes-128"

        ike_version_choices = [("v1", "v1"),
                               ("v2", "v2")]
        self.fields['ike_version'].choices = ike_version_choices

        lifetime_units_choices = [("seconds", "seconds")]
        self.fields['lifetime_units'].choices = lifetime_units_choices
        # Currently this field has only one choice, so mark it as readonly.
        self.fields['lifetime_units'].widget.attrs['readonly'] = True

        pfs_choices = [("group2", "group2"),
                       ("group5", "group5"),
                       ("group14", "group14")]
        self.fields['pfs'].choices = pfs_choices
        self.fields['pfs'].initial = "group5"

        phase1_neg_mode_choices = [("main", "main")]
        self.fields[
            'phase1_negotiation_mode'].choices = phase1_neg_mode_choices
        # Currently this field has only one choice, so mark it as readonly.
        self.fields['phase1_negotiation_mode'].widget.attrs['readonly'] = True

    class Meta(object):
        name = _("Add New IKE Policy")
        permissions = ('openstack.services.network',)
        help_text = _("Create IKE Policy for current project.\n\n"
                      "An IKE policy is an association "
                      "of the following attributes:\n\n"
                      "<li>Authorization algorithm: "
                      "Auth algorithm limited to SHA1 only.</li>"
                      "<li>Encryption algorithm: "
                      "The type of algorithm "
                      "(3des, aes-128, aes-192, aes-256) "
                      "used in the IKE Policy.</li>"
                      "<li>IKE version: The type of version (v1/v2) "
                      "that needs to be filtered.</li>"
                      "<li>Lifetime: Life time consists of units and value. "
                      "Units in 'seconds' "
                      "and the default value is 3600.</li>"
                      "<li>Perfect Forward Secrecy: "
                      "PFS limited to using Diffie-Hellman "
                      "groups 2, 5(default) and 14.</li>"
                      "<li>IKE Phase 1 negotiation mode: "
                      "Limited to 'main' mode only.</li>\n"
                      "All fields are optional."
                      )


class AddIKEPolicyStep(workflows.Step):
    action_class = AddIKEPolicyAction
    contributes = ("name", "description", "auth_algorithm",
                   "encryption_algorithm", "ike_version",
                   "lifetime_units", "lifetime_value",
                   "pfs", "phase1_negotiation_mode")

    def contribute(self, data, context):
        context = super(AddIKEPolicyStep, self).contribute(data, context)
        context['lifetime'] = {'units': data['lifetime_units'],
                               'value': data['lifetime_value']}
        context.pop('lifetime_units')
        context.pop('lifetime_value')
        if data:
            return context


class AddIKEPolicy(workflows.Workflow):
    slug = "addikepolicy"
    name = _("Add IKE Policy")
    finalize_button_name = _("Add")
    success_message = _('Added IKE Policy "%s".')
    failure_message = _('Unable to add IKE Policy "%s".')
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
    name = forms.CharField(max_length=80, label=_("Name"), required=False)
    description = forms.CharField(
        initial="", required=False,
        max_length=80, label=_("Description"))
    auth_algorithm = forms.ChoiceField(label=_("Authorization algorithm"),
                                       required=False)
    encapsulation_mode = forms.ChoiceField(label=_("Encapsulation mode"),
                                           required=False)
    encryption_algorithm = forms.ChoiceField(label=_("Encryption algorithm"),
                                             required=False)
    lifetime_units = forms.ChoiceField(label=_("Lifetime units"),
                                       required=False)
    lifetime_value = forms.IntegerField(
        min_value=60, label=_("Lifetime value for IKE keys "),
        initial=3600,
        help_text=_("Equal to or greater than 60"),
        required=False)
    pfs = forms.ChoiceField(label=_("Perfect Forward Secrecy"), required=False)
    transform_protocol = forms.ChoiceField(label=_("Transform Protocol"),
                                           required=False)

    def __init__(self, request, *args, **kwargs):
        super(AddIPSecPolicyAction, self).__init__(request, *args, **kwargs)

        auth_algorithm_choices = [("sha1", "sha1")]
        self.fields['auth_algorithm'].choices = auth_algorithm_choices
        # Currently this field has only one choice, so mark it as readonly.
        self.fields['auth_algorithm'].widget.attrs['readonly'] = True

        encapsulation_mode_choices = [("tunnel", "tunnel"),
                                      ("transport", "transport")]
        self.fields['encapsulation_mode'].choices = encapsulation_mode_choices

        encryption_algorithm_choices = [("3des", "3des"),
                                        ("aes-128", "aes-128"),
                                        ("aes-192", "aes-192"),
                                        ("aes-256", "aes-256")]
        self.fields[
            'encryption_algorithm'].choices = encryption_algorithm_choices
        self.fields['encryption_algorithm'].initial = "aes-128"

        lifetime_units_choices = [("seconds", "seconds")]
        self.fields['lifetime_units'].choices = lifetime_units_choices
        # Currently this field has only one choice, so mark it as readonly.
        self.fields['lifetime_units'].widget.attrs['readonly'] = True

        pfs_choices = [("group2", "group2"),
                       ("group5", "group5"),
                       ("group14", "group14")]
        self.fields['pfs'].choices = pfs_choices
        self.fields['pfs'].initial = "group5"

        transform_protocol_choices = [("esp", "esp"),
                                      ("ah", "ah"),
                                      ("ah-esp", "ah-esp")]
        self.fields['transform_protocol'].choices = transform_protocol_choices

    class Meta(object):
        name = _("Add New IPSec Policy")
        permissions = ('openstack.services.network',)
        help_text = _("Create IPSec Policy for current project.\n\n"
                      "An IPSec policy is an association "
                      "of the following attributes:\n\n"
                      "<li>Authorization algorithm: "
                      "Auth_algorithm limited to SHA1 only.</li>"
                      "<li>Encapsulation mode: "
                      "The type of IPsec tunnel (tunnel/transport) "
                      "to be used.</li>"
                      "<li>Encryption algorithm: "
                      "The type of algorithm "
                      "(3des, aes-128, aes-192, aes-256) "
                      "used in the IPSec Policy.</li>"
                      "<li>Lifetime: Life time consists of units and value. "
                      "Units in 'seconds' "
                      "and the default value is 3600.</li>"
                      "<li>Perfect Forward Secrecy: "
                      "PFS limited to using Diffie-Hellman "
                      "groups 2, 5(default) and 14.</li>"
                      "<li>Transform Protocol: "
                      "The type of protocol "
                      "(esp, ah, ah-esp) used in IPSec Policy.</li>\n"
                      "All fields are optional."
                      )


class AddIPSecPolicyStep(workflows.Step):
    action_class = AddIPSecPolicyAction
    contributes = ("name", "description", "auth_algorithm",
                   "encapsulation_mode", "encryption_algorithm",
                   "lifetime_units", "lifetime_value",
                   "pfs", "transform_protocol")

    def contribute(self, data, context):
        context = super(AddIPSecPolicyStep, self).contribute(data, context)
        context['lifetime'] = {'units': data['lifetime_units'],
                               'value': data['lifetime_value']}
        context.pop('lifetime_units')
        context.pop('lifetime_value')
        if data:
            return context


class AddIPSecPolicy(workflows.Workflow):
    slug = "addipsecpolicy"
    name = _("Add IPSec Policy")
    finalize_button_name = _("Add")
    success_message = _('Added IPSec Policy "%s".')
    failure_message = _('Unable to add IPSec Policy "%s".')
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
    name = forms.CharField(max_length=80, label=_("Name"), required=False)
    description = forms.CharField(
        initial="", required=False,
        max_length=80, label=_("Description"))
    vpnservice_id = forms.ChoiceField(
        label=_("VPN Service associated with this connection"))
    ikepolicy_id = forms.ChoiceField(
        label=_("IKE Policy associated with this connection"))
    ipsecpolicy_id = forms.ChoiceField(
        label=_("IPSec Policy associated with this connection"))
    peer_address = forms.IPField(
        label=_("Peer gateway public IPv4/IPv6 Address or FQDN"),
        help_text=_("Peer gateway public IPv4/IPv6 address or FQDN for "
                    "the VPN Connection"),
        version=forms.IPv4 | forms.IPv6,
        mask=False)
    peer_id = forms.IPField(
        label=_("Peer router identity for authentication (Peer ID)"),
        help_text=_("Peer router identity for authentication. "
                    "Can be IPv4/IPv6 address, e-mail, key ID, or FQDN"),
        version=forms.IPv4 | forms.IPv6,
        mask=False)
    peer_cidrs = forms.MultiIPField(
        label=_("Remote peer subnet(s)"),
        help_text=_("Remote peer subnet(s) address(es) "
                    "with mask(s) in CIDR format "
                    "separated with commas if needed "
                    "(e.g. 20.1.0.0/24, 21.1.0.0/24)"),
        version=forms.IPv4 | forms.IPv6,
        mask=True)
    psk = forms.CharField(
        max_length=80,
        label=_("Pre-Shared Key (PSK) string"),
        help_text=_("The pre-defined key string "
                    "between the two peers of the VPN connection"))

    def populate_ikepolicy_id_choices(self, request, context):
        ikepolicy_id_choices = [('', _("Select IKE Policy"))]
        try:
            tenant_id = self.request.user.tenant_id
            ikepolicies = api.vpn.ikepolicy_list(request, tenant_id=tenant_id)
        except Exception:
            exceptions.handle(request,
                              _('Unable to retrieve IKE Policies list.'))
            ikepolicies = []
        for p in ikepolicies:
            ikepolicy_id_choices.append((p.id, p.name))
        self.fields['ikepolicy_id'].choices = ikepolicy_id_choices
        return ikepolicy_id_choices

    def populate_ipsecpolicy_id_choices(self, request, context):
        ipsecpolicy_id_choices = [('', _("Select IPSec Policy"))]
        try:
            tenant_id = self.request.user.tenant_id
            ipsecpolicies = api.vpn.ipsecpolicy_list(request,
                                                     tenant_id=tenant_id)
        except Exception:
            exceptions.handle(request,
                              _('Unable to retrieve IPSec Policies list.'))
            ipsecpolicies = []
        for p in ipsecpolicies:
            ipsecpolicy_id_choices.append((p.id, p.name))
        self.fields['ipsecpolicy_id'].choices = ipsecpolicy_id_choices
        return ipsecpolicy_id_choices

    def populate_vpnservice_id_choices(self, request, context):
        vpnservice_id_choices = [('', _("Select VPN Service"))]
        try:
            tenant_id = self.request.user.tenant_id
            vpnservices = api.vpn.vpnservice_list(request, tenant_id=tenant_id)
        except Exception:
            exceptions.handle(request,
                              _('Unable to retrieve VPN Services list.'))
            vpnservices = []
        for s in vpnservices:
            vpnservice_id_choices.append((s.id, s.name))
        self.fields['vpnservice_id'].choices = vpnservice_id_choices
        return vpnservice_id_choices

    class Meta(object):
        name = _("Add New IPSec Site Connection")
        permissions = ('openstack.services.network',)
        help_text = _("Create IPSec Site Connection for current project.\n\n"
                      "Assign a name and description for the "
                      "IPSec Site Connection. "
                      "All fields in this tab are required."
                      )


class AddIPSecSiteConnectionStep(workflows.Step):
    action_class = AddIPSecSiteConnectionAction
    contributes = ("name", "description",
                   "vpnservice_id", "ikepolicy_id", "ipsecpolicy_id",
                   "peer_address", "peer_id", "peer_cidrs", "psk")


class AddIPSecSiteConnectionOptionalAction(workflows.Action):
    mtu = forms.IntegerField(
        min_value=68,
        label=_("Maximum Transmission Unit size for the connection"),
        initial=1500,
        required=False,
        help_text=_("Equal to or greater than 68 if the local subnet is IPv4. "
                    "Equal to or greater than 1280 if the local subnet "
                    "is IPv6."))
    dpd_action = forms.ChoiceField(label=_("Dead peer detection actions"),
                                   required=False)
    dpd_interval = forms.IntegerField(
        min_value=1, label=_("Dead peer detection interval"),
        initial=30,
        required=False,
        help_text=_("Valid integer lesser than DPD timeout"))
    dpd_timeout = forms.IntegerField(
        min_value=1, label=_("Dead peer detection timeout"),
        initial=120,
        required=False,
        help_text=_("Valid integer greater than the DPD interval"))
    initiator = forms.ChoiceField(label=_("Initiator state"), required=False)
    admin_state_up = forms.ChoiceField(
        choices=[(True, _('UP')), (False, _('DOWN'))],
        label=_("Admin State"),
        required=False,
        help_text=_("The state of IPSec site connection to start in. "
                    "If DOWN (False), IPSec site connection "
                    "does not forward packets."))

    def __init__(self, request, *args, **kwargs):
        super(AddIPSecSiteConnectionOptionalAction, self).__init__(
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

    def clean(self):
        cleaned_data = super(AddIPSecSiteConnectionOptionalAction,
                             self).clean()
        interval = cleaned_data.get('dpd_interval')
        timeout = cleaned_data.get('dpd_timeout')

        if not interval < timeout:
            msg = _("DPD Timeout must be greater than DPD Interval")
            self._errors['dpd_timeout'] = self.error_class([msg])
        return cleaned_data

    class Meta(object):
        name = _("Optional Parameters")
        permissions = ('openstack.services.network',)
        help_text = _("Fields in this tab are optional. "
                      "You can configure the detail of "
                      "IPSec site connection created."
                      )


class AddIPSecSiteConnectionOptionalStep(workflows.Step):
    action_class = AddIPSecSiteConnectionOptionalAction
    contributes = ("dpd_action", "dpd_interval", "dpd_timeout",
                   "initiator", "mtu", "admin_state_up")

    def contribute(self, data, context):
        context = super(
            AddIPSecSiteConnectionOptionalStep, self).contribute(data, context)
        context['dpd'] = {'action': data['dpd_action'],
                          'interval': data['dpd_interval'],
                          'timeout': data['dpd_timeout']}
        context.pop('dpd_action')
        context.pop('dpd_interval')
        context.pop('dpd_timeout')

        cidrs = context['peer_cidrs']
        context['peer_cidrs'] = cidrs.replace(" ", "").split(",")

        if data:
            return context


class AddIPSecSiteConnection(workflows.Workflow):
    slug = "addipsecsiteconnection"
    name = _("Add IPSec Site Connection")
    finalize_button_name = _("Add")
    success_message = _('Added IPSec Site Connection "%s".')
    failure_message = _('Unable to add IPSec Site Connection "%s".')
    success_url = "horizon:project:vpn:index"
    default_steps = (AddIPSecSiteConnectionStep,
                     AddIPSecSiteConnectionOptionalStep)

    def format_status_message(self, message):
        return message % self.context.get('name')

    def handle(self, request, context):
        try:
            api.vpn.ipsecsiteconnection_create(request, **context)
            return True
        except Exception:
            return False
