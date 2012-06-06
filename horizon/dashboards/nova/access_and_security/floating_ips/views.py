# vim: tabstop=4 shiftwidth=4 softtabstop=4

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
Views for managing Nova floating IPs.
"""

from django.utils.translation import ugettext_lazy as _

from horizon import api
from horizon import exceptions
from horizon import forms
from horizon import workflows
from .forms import FloatingIpAllocate
from .workflows import IPAssociationWorkflow


class AssociateView(workflows.WorkflowView):
    workflow_class = IPAssociationWorkflow
    template_name = "nova/access_and_security/floating_ips/associate.html"


class AllocateView(forms.ModalFormView):
    form_class = FloatingIpAllocate
    template_name = 'nova/access_and_security/floating_ips/allocate.html'
    context_object_name = 'floating_ip'

    def get_context_data(self, **kwargs):
        context = super(AllocateView, self).get_context_data(**kwargs)
        try:
            context['usages'] = api.tenant_quota_usages(self.request)
        except:
            exceptions.handle(self.request)
        return context

    def get_initial(self):
        pools = api.floating_ip_pools_list(self.request)
        if pools:
            pool_list = [(pool.name, pool.name)
                         for pool in api.floating_ip_pools_list(self.request)]
        else:
            pool_list = [(None, _("No floating IP pools available."))]
        return {'tenant_name': self.request.user.tenant_name,
                'pool_list': pool_list}
