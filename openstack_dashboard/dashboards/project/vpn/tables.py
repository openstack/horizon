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


from django.core.urlresolvers import reverse
from django.template.defaultfilters import title  # noqa
from django.utils.translation import ugettext_lazy as _

from horizon import tables
from horizon.utils import filters


forbid_updates = set(["PENDING_CREATE", "PENDING_UPDATE", "PENDING_DELETE"])


class AddIKEPolicyLink(tables.LinkAction):
    name = "addikepolicy"
    verbose_name = _("Add IKE Policy")
    url = "horizon:project:vpn:addikepolicy"
    classes = ("ajax-modal",)
    icon = "plus"
    policy_rules = (("network", "create_ikepolicy"),)


class AddIPSecPolicyLink(tables.LinkAction):
    name = "addipsecpolicy"
    verbose_name = _("Add IPSec Policy")
    url = "horizon:project:vpn:addipsecpolicy"
    classes = ("ajax-modal",)
    icon = "plus"
    policy_rules = (("network", "create_ipsecpolicy"),)


class AddVPNServiceLink(tables.LinkAction):
    name = "addvpnservice"
    verbose_name = _("Add VPN Service")
    url = "horizon:project:vpn:addvpnservice"
    classes = ("ajax-modal",)
    icon = "plus"
    policy_rules = (("network", "create_vpnservice"),)


class AddIPSecSiteConnectionLink(tables.LinkAction):
    name = "addipsecsiteconnection"
    verbose_name = _("Add IPSec Site Connection")
    url = "horizon:project:vpn:addipsecsiteconnection"
    classes = ("ajax-modal",)
    icon = "plus"
    policy_rules = (("network", "create_ipsec_site_connection"),)


class DeleteVPNServiceLink(tables.DeleteAction):
    name = "deletevpnservice"
    action_present = _("Delete")
    action_past = _("Scheduled deletion of %(data_type)s")
    data_type_singular = _("VPN Service")
    data_type_plural = _("VPN Services")
    policy_rules = (("network", "delete_vpnservice"),)

    def allowed(self, request, datum=None):
        if datum and datum.ipsecsiteconns:
            return False
        return True


class DeleteIKEPolicyLink(tables.DeleteAction):
    name = "deleteikepolicy"
    action_present = _("Delete")
    action_past = _("Scheduled deletion of %(data_type)s")
    data_type_singular = _("IKE Policy")
    data_type_plural = _("IKE Policies")
    policy_rules = (("network", "delete_ikepolicy"),)

    def allowed(self, request, datum=None):
        if datum and datum.ipsecsiteconns:
            return False
        return True


class DeleteIPSecPolicyLink(tables.DeleteAction):
    name = "deleteipsecpolicy"
    action_present = _("Delete")
    action_past = _("Scheduled deletion of %(data_type)s")
    data_type_singular = _("IPSec Policy")
    data_type_plural = _("IPSec Policies")
    policy_rules = (("network", "delete_ipsecpolicy"),)

    def allowed(self, request, datum=None):
        if datum and datum.ipsecsiteconns:
            return False
        return True


class DeleteIPSecSiteConnectionLink(tables.DeleteAction):
    name = "deleteipsecsiteconnection"
    action_present = _("Delete")
    action_past = _("Scheduled deletion of %(data_type)s")
    data_type_singular = _("IPSec Site Connection")
    data_type_plural = _("IPSec Site Connections")
    policy_rules = (("network", "delete_ipsec_site_connection"),)


class UpdateVPNServiceLink(tables.LinkAction):
    name = "update_vpnservice"
    verbose_name = _("Edit VPN Service")
    classes = ("ajax-modal", "btn-update",)
    policy_rules = (("network", "update_vpnservice"),)

    def get_link_url(self, vpnservice):
        return reverse("horizon:project:vpn:update_vpnservice",
                       kwargs={'vpnservice_id': vpnservice.id})

    def allowed(self, request, datum=None):
        if datum and datum.status not in forbid_updates:
            return True
        return False


class UpdateIKEPolicyLink(tables.LinkAction):
    name = "updateikepolicy"
    verbose_name = _("Edit IKE Policy")
    classes = ("ajax-modal", "btn-update",)
    policy_rules = (("network", "update_ikepolicy"),)

    def get_link_url(self, ikepolicy):
        return reverse("horizon:project:vpn:update_ikepolicy",
                       kwargs={'ikepolicy_id': ikepolicy.id})

    def allowed(self, request, datum=None):
        return not datum['ipsecsiteconns']


class UpdateIPSecPolicyLink(tables.LinkAction):
    name = "updateipsecpolicy"
    verbose_name = _("Edit IPSec Policy")
    classes = ("ajax-modal", "btn-update",)
    policy_rules = (("network", "update_ipsecpolicy"),)

    def get_link_url(self, ipsecpolicy):
        return reverse("horizon:project:vpn:update_ipsecpolicy",
                       kwargs={'ipsecpolicy_id': ipsecpolicy.id})

    def allowed(self, request, datum=None):
        return not datum['ipsecsiteconns']


class UpdateIPSecSiteConnectionLink(tables.LinkAction):
    name = "updateipsecsiteconnection"
    verbose_name = _("Edit Connection")
    classes = ("ajax-modal", "btn-update",)
    policy_rules = (("network", "update_ipsec_site_connection"),)

    def get_link_url(self, ipsecsiteconnection):
        return reverse("horizon:project:vpn:update_ipsecsiteconnection",
            kwargs={'ipsecsiteconnection_id': ipsecsiteconnection.id})

    def allowed(self, request, datum=None):
        if datum and datum.status not in forbid_updates:
            return True
        return False


class IPSecSiteConnectionsTable(tables.DataTable):
    STATUS_CHOICES = (
        ("Active", True),
        ("Down", True),
        ("Error", False),
    )
    id = tables.Column('id', hidden=True)
    name = tables.Column('name', verbose_name=_('Name'),
                         link="horizon:project:vpn:ipsecsiteconnectiondetails")
    vpnservice_name = tables.Column('vpnservice_name',
                                    verbose_name=_('VPN Service'))
    ikepolicy_name = tables.Column('ikepolicy_name',
                                   verbose_name=_('IKE Policy'))
    ipsecpolicy_name = tables.Column('ipsecpolicy_name',
                                     verbose_name=_('IPSec Policy'))
    status = tables.Column("status",
                           filters=(title, filters.replace_underscores),
                           verbose_name=_("Status"),
                           status=True,
                           status_choices=STATUS_CHOICES)

    class Meta:
        name = "ipsecsiteconnectionstable"
        verbose_name = _("IPSec Site Connections")
        table_actions = (AddIPSecSiteConnectionLink,
                         DeleteIPSecSiteConnectionLink)
        row_actions = (UpdateIPSecSiteConnectionLink,
                       DeleteIPSecSiteConnectionLink)


class VPNServicesTable(tables.DataTable):
    STATUS_CHOICES = (
        ("Active", True),
        ("Down", True),
        ("Error", False),
    )
    id = tables.Column('id', hidden=True)
    name = tables.Column("name", verbose_name=_('Name'),
                         link="horizon:project:vpn:vpnservicedetails")
    description = tables.Column('description', verbose_name=_('Description'))
    subnet_name = tables.Column('subnet_name', verbose_name=_('Subnet'))
    router_name = tables.Column('router_name', verbose_name=_('Router'))
    status = tables.Column("status",
                           filters=(title, filters.replace_underscores),
                           verbose_name=_("Status"),
                           status=True,
                           status_choices=STATUS_CHOICES)

    class Meta:
        name = "vpnservicestable"
        verbose_name = _("VPN Services")
        table_actions = (AddVPNServiceLink, DeleteVPNServiceLink)
        row_actions = (UpdateVPNServiceLink, DeleteVPNServiceLink)


class IKEPoliciesTable(tables.DataTable):
    id = tables.Column('id', hidden=True)
    name = tables.Column("name", verbose_name=_('Name'),
                         link="horizon:project:vpn:ikepolicydetails")
    auth_algorithm = tables.Column('auth_algorithm',
                                   verbose_name=_('Authorization algorithm'))
    encryption_algorithm = tables.Column(
        'encryption_algorithm',
        verbose_name=_('Encryption algorithm'))
    pfs = tables.Column("pfs", verbose_name=_('PFS'))

    class Meta:
        name = "ikepoliciestable"
        verbose_name = _("IKE Policies")
        table_actions = (AddIKEPolicyLink, DeleteIKEPolicyLink)
        row_actions = (UpdateIKEPolicyLink, DeleteIKEPolicyLink)


class IPSecPoliciesTable(tables.DataTable):
    id = tables.Column('id', hidden=True)
    name = tables.Column("name", verbose_name=_('Name'),
                         link="horizon:project:vpn:ipsecpolicydetails")
    auth_algorithm = tables.Column('auth_algorithm',
                                   verbose_name=_('Authorization algorithm'))
    encryption_algorithm = tables.Column(
        'encryption_algorithm',
        verbose_name=_('Encryption algorithm'))
    pfs = tables.Column("pfs", verbose_name=_('PFS'))

    class Meta:
        name = "ipsecpoliciestable"
        verbose_name = _("IPSec Policies")
        table_actions = (AddIPSecPolicyLink, DeleteIPSecPolicyLink,)
        row_actions = (UpdateIPSecPolicyLink, DeleteIPSecPolicyLink)
