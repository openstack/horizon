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


from django.utils.translation import ugettext_lazy as _  # noqa

from horizon import exceptions
from horizon import messages
from horizon import tabs
from horizon import workflows

from openstack_dashboard import api

from openstack_dashboard.dashboards.project.vpn import tabs as vpn_tabs
from openstack_dashboard.dashboards.project.vpn import \
    workflows as vpn_workflow

import re


class IndexView(tabs.TabbedTableView):
    tab_group_class = vpn_tabs.VPNTabs
    template_name = 'project/vpn/index.html'

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
                                     _('Deleted VPN Service %s' % obj_id))
                except Exception:
                    exceptions.handle(request,
                                      _('Unable to delete VPN Service.'))
        elif m == 'ikepolicy':
            for obj_id in obj_ids:
                try:
                    api.vpn.ikepolicy_delete(request, obj_id)
                    messages.success(request,
                                     _('Deleted IKE Policy %s' % obj_id))
                except Exception:
                    exceptions.handle(request,
                                      _('Unable to delete IKE Policy.'))
        elif m == 'ipsecpolicy':
            for obj_id in obj_ids:
                try:
                    api.vpn.ipsecpolicy_delete(request, obj_id)
                    messages.success(request,
                                     _('Deleted IPSec Policy %s' % obj_id))
                except Exception:
                    exceptions.handle(request,
                                      _('Unable to delete IPSec Policy.'))
        elif m == 'ipsecsiteconnection':
            for obj_id in obj_ids:
                try:
                    api.vpn.ipsecsiteconnection_delete(request, obj_id)
                    messages.success(request,
                                     _('Deleted IPSec Site Connection %s'
                                     % obj_id))
                except Exception:
                    exceptions.handle(request,
                        _('Unable to delete IPSec Site Connection.'))

        return self.get(request, *args, **kwargs)


class AddVPNServiceView(workflows.WorkflowView):
    workflow_class = vpn_workflow.AddVPNService

    def get_initial(self):
        initial = super(AddVPNServiceView, self).get_initial()
        return initial


class AddIPSecSiteConnectionView(workflows.WorkflowView):
    workflow_class = vpn_workflow.AddIPSecSiteConnection

    def get_initial(self):
        initial = super(AddIPSecSiteConnectionView, self).get_initial()
        return initial


class AddIKEPolicyView(workflows.WorkflowView):
    workflow_class = vpn_workflow.AddIKEPolicy

    def get_initial(self):
        initial = super(AddIKEPolicyView, self).get_initial()
        return initial


class AddIPSecPolicyView(workflows.WorkflowView):
    workflow_class = vpn_workflow.AddIPSecPolicy

    def get_initial(self):
        initial = super(AddIPSecPolicyView, self).get_initial()
        return initial


class IKEPolicyDetailsView(tabs.TabView):
    tab_group_class = (vpn_tabs.IKEPolicyDetailsTabs)
    template_name = 'project/vpn/details_tabs.html'


class IPSecPolicyDetailsView(tabs.TabView):
    tab_group_class = (vpn_tabs.IPSecPolicyDetailsTabs)
    template_name = 'project/vpn/details_tabs.html'


class VPNServiceDetailsView(tabs.TabView):
    tab_group_class = (vpn_tabs.VPNServiceDetailsTabs)
    template_name = 'project/vpn/details_tabs.html'


class IPSecSiteConnectionDetailsView(tabs.TabView):
    tab_group_class = (vpn_tabs.IPSecSiteConnectionDetailsTabs)
    template_name = 'project/vpn/details_tabs.html'
