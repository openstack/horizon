# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright 2011 United States Government as represented by the
# Administrator of the National Aeronautics and Space Administration.
# All Rights Reserved.
#
# Copyright 2011 Nebula, Inc.
# Copyright (c) 2011 X.commerce, a business unit of eBay Inc.
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

from django.contrib import messages
from django.utils.translation import ugettext as _

from horizon import api
from horizon import forms
from .forms import FloatingIpAssociate, FloatingIpAllocate


LOG = logging.getLogger(__name__)


class AssociateView(forms.ModalFormView):
    form_class = FloatingIpAssociate
    template_name = 'nova/access_and_security/floating_ips/associate.html'
    context_object_name = 'floating_ip'

    def get_object(self, *args, **kwargs):
        ip_id = kwargs['ip_id']
        try:
            return api.tenant_floating_ip_get(self.request, ip_id)
        except Exception as e:
            LOG.exception('Error fetching floating ip with id "%s".' % ip_id)
            messages.error(self.request,
                           _('Unable to associate floating ip: %s') % e)
            raise http.Http404("Floating IP %s not available." % ip_id)

    def get_initial(self):
        instances = [(server.id, 'id: %s, name: %s' %
                        (server.id, server.name))
                        for server in api.server_list(self.request)]
        return {'floating_ip_id': self.object.id,
                'floating_ip': self.object.ip,
                'instances': instances}


class AllocateView(forms.ModalFormView):
    form_class = FloatingIpAllocate
    template_name = 'nova/access_and_security/floating_ips/allocate.html'
    context_object_name = 'floating_ip'

    def get_initial(self):
        pools = api.floating_ip_pools_list(self.request)
        if pools:
            pool_list = [(pool.name, pool.name)
                         for pool in api.floating_ip_pools_list(self.request)]
        else:
            pool_list = [(None, _("There are no Floating IP Pools"))]
        return {'tenant_id': self.request.user.tenant_id,
                'pool_list': pool_list}
