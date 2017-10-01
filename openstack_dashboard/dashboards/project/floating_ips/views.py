# Copyright 2012 United States Government as represented by the
# Administrator of the National Aeronautics and Space Administration.
# All Rights Reserved.
#
# Copyright 2012 Nebula, Inc.
# Copyright (c) 2012 X.commerce, a business unit of eBay Inc.
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
Views for managing floating IPs.
"""

from django.core.urlresolvers import reverse_lazy
from django.utils.translation import ugettext_lazy as _

from neutronclient.common import exceptions as neutron_exc

from horizon import exceptions
from horizon import forms
from horizon import tables
from horizon import workflows

from openstack_dashboard import api
from openstack_dashboard.usage import quotas

from openstack_dashboard.dashboards.project.floating_ips \
    import forms as project_forms
from openstack_dashboard.dashboards.project.floating_ips \
    import tables as project_tables
from openstack_dashboard.dashboards.project.floating_ips \
    import workflows as project_workflows


class AssociateView(workflows.WorkflowView):
    workflow_class = project_workflows.IPAssociationWorkflow


class AllocateView(forms.ModalFormView):
    form_class = project_forms.FloatingIpAllocate
    form_id = "associate_floating_ip_form"
    page_title = _("Allocate Floating IP")
    template_name = 'project/floating_ips/allocate.html'
    submit_label = _("Allocate IP")
    submit_url = reverse_lazy("horizon:project:floating_ips:allocate")
    success_url = reverse_lazy('horizon:project:floating_ips:index')

    def get_object_display(self, obj):
        return obj.ip

    def get_context_data(self, **kwargs):
        context = super(AllocateView, self).get_context_data(**kwargs)
        try:
            context['usages'] = quotas.tenant_quota_usages(
                self.request, targets=('floating_ips', ))
        except Exception:
            exceptions.handle(self.request)
        return context

    def get_initial(self):
        try:
            pools = api.neutron.floating_ip_pools_list(self.request)
        except neutron_exc.ConnectionFailed:
            pools = []
            exceptions.handle(self.request)
        except Exception:
            pools = []
            exceptions.handle(self.request,
                              _("Unable to retrieve floating IP pools."))
        pool_list = [(pool.id, pool.name) for pool in pools]
        if not pool_list:
            pool_list = [(None, _("No floating IP pools available"))]
        return {'pool_list': pool_list}


class IndexView(tables.DataTableView):
    table_class = project_tables.FloatingIPsTable
    page_title = _("Floating IPs")

    def get_data(self):
        try:
            floating_ips = api.neutron.tenant_floating_ip_list(self.request)
        except neutron_exc.ConnectionFailed:
            floating_ips = []
            exceptions.handle(self.request)
        except Exception:
            floating_ips = []
            exceptions.handle(self.request,
                              _('Unable to retrieve floating IP addresses.'))

        try:
            floating_ip_pools = \
                api.neutron.floating_ip_pools_list(self.request)
        except neutron_exc.ConnectionFailed:
            floating_ip_pools = []
            exceptions.handle(self.request)
        except Exception:
            floating_ip_pools = []
            exceptions.handle(self.request,
                              _('Unable to retrieve floating IP pools.'))
        pool_dict = dict([(obj.id, obj.name) for obj in floating_ip_pools])

        attached_instance_ids = [ip.instance_id for ip in floating_ips
                                 if ip.instance_id is not None]
        instances_dict = {}
        if attached_instance_ids:
            instances = []
            try:
                # TODO(tsufiev): we should pass attached_instance_ids to
                # nova.server_list as soon as Nova API allows for this
                instances, has_more = api.nova.server_list(self.request,
                                                           detailed=False)
            except Exception:
                exceptions.handle(self.request,
                                  _('Unable to retrieve instance list.'))

            instances_dict = dict([(obj.id, obj.name) for obj in instances])

        for ip in floating_ips:
            ip.instance_name = instances_dict.get(ip.instance_id)
            ip.pool_name = pool_dict.get(ip.pool, ip.pool)

        return floating_ips
