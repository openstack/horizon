# Copyright 2015, Thales Services SAS
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

from django.core.urlresolvers import reverse
from django.utils.translation import ugettext_lazy as _

from horizon import exceptions
from horizon import forms
from horizon import messages

from neutronclient.common import exceptions as neutron_exc

from openstack_dashboard.api import neutron as api

LOG = logging.getLogger(__name__)


class AddRouterRoute(forms.SelfHandlingForm):
    destination = forms.IPField(label=_("Destination CIDR"), mask=True)
    nexthop = forms.IPField(label=_("Next Hop"))
    failure_url = 'horizon:project:routers:detail'

    def handle(self, request, data, **kwargs):
        router_id = self.initial['router_id']
        try:
            route = {'nexthop': data['nexthop'],
                     'destination': data['destination']}
            api.router_static_route_add(request,
                                        router_id,
                                        route)
            msg = _('Static route added')
            messages.success(request, msg)
            return True
        except neutron_exc.BadRequest as e:
            LOG.info('Invalid format for routes %(route)s: %(exc)s',
                     {'route': route, 'exc': e})
            msg = _('Invalid format for routes: %s') % e
            messages.error(request, msg)
            redirect = reverse(self.failure_url, args=[router_id])
            exceptions.handle(request, msg, redirect=redirect)
        except Exception as e:
            LOG.info('Failed to add route: %s', e)
            msg = _('Failed to add route: %s') % e
            messages.error(request, msg)
            redirect = reverse(self.failure_url, args=[router_id])
            exceptions.handle(request, msg, redirect=redirect)
