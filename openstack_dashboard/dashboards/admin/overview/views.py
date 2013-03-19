# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright 2012 United States Government as represented by the
# Administrator of the National Aeronautics and Space Administration.
# All Rights Reserved.
#
# Copyright 2012 Nebula, Inc.
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

from django.conf import settings
from django.utils.translation import ugettext as _

from horizon import exceptions

from openstack_dashboard import api
from openstack_dashboard import usage


class GlobalOverview(usage.UsageView):
    table_class = usage.GlobalUsageTable
    usage_class = usage.GlobalUsage
    template_name = 'admin/overview/usage.html'

    def get_context_data(self, **kwargs):
        context = super(GlobalOverview, self).get_context_data(**kwargs)
        context['monitoring'] = getattr(settings, 'EXTERNAL_MONITORING', [])
        return context

    def get_data(self):
        data = super(GlobalOverview, self).get_data()
        # Pre-fill tenant names
        try:
            tenants = api.keystone.tenant_list(self.request, admin=True)
        except:
            tenants = []
            exceptions.handle(self.request,
                              _('Unable to retrieve project list.'))
        for instance in data:
            tenant = filter(lambda t: t.id == instance.tenant_id, tenants)
            if tenant:
                instance.tenant_name = getattr(tenant[0], "name", None)
            else:
                instance.tenant_name = None
        return data
