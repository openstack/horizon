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
import logging

from django.core.urlresolvers import reverse
from django.utils.translation import ugettext_lazy as _

from horizon import api
from horizon import exceptions
from horizon import forms
from .forms import FloatingIpAssociate, FloatingIpAllocate


LOG = logging.getLogger(__name__)


class AssociateView(forms.ModalFormView):
    form_class = FloatingIpAssociate
    template_name = 'nova/access_and_security/floating_ips/associate.html'
    context_object_name = 'floating_ip'

    def get_object(self, *args, **kwargs):
        ip_id = int(kwargs['ip_id'])
        try:
            return api.tenant_floating_ip_get(self.request, ip_id)
        except:
            redirect = reverse('horizon:nova:access_and_security:index')
            exceptions.handle(self.request,
                              _('Unable to associate floating IP.'),
                              redirect=redirect)

    def get_initial(self):
        try:
            servers = api.server_list(self.request)
        except:
            redirect = reverse('horizon:nova:access_and_security:index')
            exceptions.handle(self.request,
                              _('Unable to retrieve instance list.'),
                              redirect=redirect)
        instances = []
        for server in servers:
            # FIXME(ttrifonov): show IP in case of non-unique names
            # to be removed when nova can support unique names
            server_name = server.name
            if any(s.id != server.id and
                   s.name == server.name for s in servers):
                # duplicate instance name
                server_name = "%s [%s]" % (server.name, server.id)
            instances.append((server.id, server_name))

        # Sort instances for easy browsing
        instances = sorted(instances, key=lambda x: x[1])

        return {'floating_ip_id': self.object.id,
                'floating_ip': self.object.ip,
                'instances': instances}


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
