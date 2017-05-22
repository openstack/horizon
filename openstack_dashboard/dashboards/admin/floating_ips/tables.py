# Copyright 2016 Letv Cloud Computing
# All Rights Reserved.
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

import logging

from django import shortcuts
from django.utils.translation import ugettext_lazy as _

from horizon import exceptions
from horizon import messages
from horizon import tables

from openstack_dashboard import api
from openstack_dashboard.dashboards.project.floating_ips \
    import tables as project_tables
from openstack_dashboard import policy
from openstack_dashboard.utils import filters


LOG = logging.getLogger(__name__)


class FloatingIPFilterAction(tables.FilterAction):

    def filter(self, table, fips, filter_string):
        """Naive case-insensitive search."""
        q = filter_string.lower()
        return [ip for ip in fips
                if q in ip.ip.lower()]


class AdminAllocateFloatingIP(project_tables.AllocateIP):
    url = "horizon:admin:floating_ips:allocate"

    def single(self, data_table, request, *args):
        return shortcuts.redirect('horizon:admin:floating_ips:index')

    def allowed(self, request, fip=None):
        policy_rules = (("network", "create_floatingip"),)
        return policy.check(policy_rules, request)


class AdminReleaseFloatingIP(project_tables.ReleaseIPs):
    pass


class AdminSimpleDisassociateIP(project_tables.DisassociateIP):

    def single(self, table, request, obj_id):
        try:
            fip = table.get_object_by_id(filters.get_int_or_uuid(obj_id))
            api.neutron.floating_ip_disassociate(request, fip.id)
            LOG.info('Disassociating Floating IP "%s".', obj_id)
            messages.success(request,
                             _('Successfully disassociated Floating IP: %s')
                             % fip.ip)
        except Exception:
            exceptions.handle(request,
                              _('Unable to disassociate floating IP.'))
        return shortcuts.redirect('horizon:admin:floating_ips:index')


class FloatingIPsTable(project_tables.FloatingIPsTable):
    tenant = tables.Column("tenant_name", verbose_name=_("Project"))
    ip = tables.Column("ip",
                       link=("horizon:admin:floating_ips:detail"),
                       verbose_name=_("IP Address"),
                       attrs={'data-type': "ip"})

    class Meta(object):
        name = "floating_ips"
        verbose_name = _("Floating IPs")
        status_columns = ["status"]
        table_actions = (FloatingIPFilterAction,
                         AdminAllocateFloatingIP,
                         AdminReleaseFloatingIP)
        row_actions = (AdminSimpleDisassociateIP,
                       AdminReleaseFloatingIP)
        columns = ('tenant', 'ip', 'fixed_ip', 'pool', 'status')
