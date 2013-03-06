# vim: tabstop=4 shiftwidth=4 softtabstop=4

#    Copyright 2013, Big Switch Networks, Inc.
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
import re

from django import http
from django.utils.translation import ugettext as _

from horizon import exceptions
from horizon import tables
from horizon import tabs
from horizon import workflows

from openstack_dashboard import api

from .workflows import AddPool, AddMember, AddMonitor, AddVip
from .tabs import LoadBalancerTabs, PoolDetailsTabs, VipDetailsTabs
from .tabs import MemberDetailsTabs, MonitorDetailsTabs
from .tables import DeleteMonitorLink


LOG = logging.getLogger(__name__)


class IndexView(tabs.TabView):
    tab_group_class = (LoadBalancerTabs)
    template_name = 'project/loadbalancers/details_tabs.html'

    def post(self, request, *args, **kwargs):
        obj_ids = request.POST.getlist('object_ids')
        action = request.POST['action']
        m = re.search('.delete([a-z]+)', action).group(1)
        if obj_ids == []:
            obj_ids.append(re.search('([0-9a-z-]+)$', action).group(1))
        if m == 'monitor':
            for obj_id in obj_ids:
                try:
                    api.lbaas.pool_health_monitor_delete(request, obj_id)
                except:
                    exceptions.handle(request,
                                      _('Unable to delete monitor.'))
        if m == 'pool':
            for obj_id in obj_ids:
                try:
                    api.lbaas.pool_delete(request, obj_id)
                except:
                    exceptions.handle(request,
                                      _('Must delete Vip first.'))
        if m == 'member':
            for obj_id in obj_ids:
                try:
                    api.lbaas.member_delete(request, obj_id)
                except:
                    exceptions.handle(request,
                                      _('Unable to delete member.'))
        if m == 'vip':
            for obj_id in obj_ids:
                try:
                    vip_id = api.lbaas.pool_get(request, obj_id).vip_id
                except:
                    exceptions.handle(request,
                                      _('Unable to locate vip to delete.'))
                if vip_id is not None:
                    try:
                        api.lbaas.vip_delete(request, vip_id)
                    except:
                        exceptions.handle(request,
                                          _('Unable to delete vip.'))
        return self.get(request, *args, **kwargs)


class AddPoolView(workflows.WorkflowView):
    workflow_class = AddPool
    template_name = "project/loadbalancers/addpool.html"

    def get_initial(self):
        initial = super(AddPoolView, self).get_initial()
        return initial


class AddVipView(workflows.WorkflowView):
    workflow_class = AddVip
    template_name = "project/loadbalancers/addvip.html"

    def get_context_data(self, **kwargs):
        context = super(AddVipView, self).get_context_data(**kwargs)
        return context

    def get_initial(self):
        initial = super(AddVipView, self).get_initial()
        initial['pool_id'] = self.kwargs['pool_id']
        try:
            pool = api.lbaas.pool_get(self.request, initial['pool_id'])
            initial['subnet'] = api.quantum.subnet_get(
                self.request, pool.subnet_id).cidr
        except:
            initial['subnet'] = ''
            msg = _('Unable to retrieve pool subnet.')
            exceptions.handle(self.request, msg)
        return initial


class AddMemberView(workflows.WorkflowView):
    workflow_class = AddMember
    template_name = "project/loadbalancers/addmember.html"

    def get_initial(self):
        initial = super(AddMemberView, self).get_initial()
        return initial


class AddMonitorView(workflows.WorkflowView):
    workflow_class = AddMonitor
    template_name = "project/loadbalancers/addmonitor.html"

    def get_initial(self):
        initial = super(AddMonitorView, self).get_initial()
        return initial


class PoolDetailsView(tabs.TabView):
    tab_group_class = (PoolDetailsTabs)
    template_name = 'project/loadbalancers/details_tabs.html'


class VipDetailsView(tabs.TabView):
    tab_group_class = (VipDetailsTabs)
    template_name = 'project/loadbalancers/details_tabs.html'


class MemberDetailsView(tabs.TabView):
    tab_group_class = (MemberDetailsTabs)
    template_name = 'project/loadbalancers/details_tabs.html'


class MonitorDetailsView(tabs.TabView):
    tab_group_class = (MonitorDetailsTabs)
    template_name = 'project/loadbalancers/details_tabs.html'
