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


from django.template.defaultfilters import title  # noqa
from django.utils.translation import ugettext_lazy as _  # noqa

from horizon import tables
from horizon.utils import filters


class AddIKEPolicyLink(tables.LinkAction):
    name = "addikepolicy"
    verbose_name = _("Add IKE Policy")
    url = "horizon:project:vpn:addikepolicy"
    classes = ("ajax-modal", "btn-addikepolicy",)


class AddIPSecPolicyLink(tables.LinkAction):
    name = "addipsecpolicy"
    verbose_name = _("Add IPSec Policy")
    url = "horizon:project:vpn:addipsecpolicy"
    classes = ("ajax-modal", "btn-addipsecpolicy",)


class AddVPNServiceLink(tables.LinkAction):
    name = "addvpnservice"
    verbose_name = _("Add VPN Service")
    url = "horizon:project:vpn:addvpnservice"
    classes = ("ajax-modal", "btn-addvpnservice",)


class AddIPSecSiteConnectionLink(tables.LinkAction):
    name = "addipsecsiteconnection"
    verbose_name = _("Add IPSec Site Connection")
    url = "horizon:project:vpn:addipsecsiteconnection"
    classes = ("ajax-modal", "btn-addipsecsiteconnection",)


class DeleteVPNServiceLink(tables.DeleteAction):
    name = "deletevpnservice"
    action_present = _("Delete")
    action_past = _("Scheduled deletion of")
    data_type_singular = _("VPN Service")
    data_type_plural = _("VPN Services")


class DeleteIKEPolicyLink(tables.DeleteAction):
    name = "deleteikepolicy"
    action_present = _("Delete")
    action_past = _("Scheduled deletion of")
    data_type_singular = _("IKE Policy")
    data_type_plural = _("IKE Policies")


class DeleteIPSecPolicyLink(tables.DeleteAction):
    name = "deleteipsecpolicy"
    action_present = _("Delete")
    action_past = _("Scheduled deletion of")
    data_type_singular = _("IPSec Policy")
    data_type_plural = _("IPSec Policies")


class DeleteIPSecSiteConnectionLink(tables.DeleteAction):
    name = "deleteipsecsiteconnection"
    action_present = _("Delete")
    action_past = _("Scheduled deletion of")
    data_type_singular = _("IPSec Site Connection")
    data_type_plural = _("IPSec Site Connections")


class IPSecSiteConnectionsTable(tables.DataTable):
    STATUS_CHOICES = (
        ("Active", True),
        ("Down", True),
        ("Error", False),
    )
    id = tables.Column('id', verbose_name=_('Id'), hidden=True)
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
        row_actions = (DeleteIPSecSiteConnectionLink,)


class VPNServicesTable(tables.DataTable):
    STATUS_CHOICES = (
        ("Active", True),
        ("Down", True),
        ("Error", False),
    )
    id = tables.Column('id', verbose_name=_('Id'), hidden=True)
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
        row_actions = (DeleteVPNServiceLink,)


class IKEPoliciesTable(tables.DataTable):
    id = tables.Column('id', verbose_name=_('Id'), hidden=True)
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
        row_actions = (DeleteIKEPolicyLink,)


class IPSecPoliciesTable(tables.DataTable):
    id = tables.Column('id', verbose_name=_('Id'), hidden=True)
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
        row_actions = (DeleteIPSecPolicyLink,)
