# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright 2013 Hewlett-Packard Development Company, L.P.
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

from django.core.urlresolvers import reverse
from django.utils.translation import ugettext_lazy as _

from horizon import exceptions
from horizon import tables
from horizon import workflows

from openstack_dashboard import api

from .constants import DOMAIN_INFO_FIELDS
from .constants import DOMAINS_INDEX_URL
from .constants import DOMAINS_INDEX_VIEW_TEMPLATE
from .tables import DomainsTable
from .workflows import CreateDomain
from .workflows import UpdateDomain


class IndexView(tables.DataTableView):
    table_class = DomainsTable
    template_name = DOMAINS_INDEX_VIEW_TEMPLATE

    def get_data(self):
        domains = []
        try:
            domains = api.keystone.domain_list(self.request)
        except:
            exceptions.handle(self.request,
                              _('Unable to retrieve domain list.'))
        return domains


class CreateDomainView(workflows.WorkflowView):
    workflow_class = CreateDomain


class UpdateDomainView(workflows.WorkflowView):
    workflow_class = UpdateDomain

    def get_initial(self):
        initial = super(UpdateDomainView, self).get_initial()

        domain_id = self.kwargs['domain_id']
        initial['domain_id'] = domain_id

        try:
            # get initial domain info
            domain_info = api.keystone.domain_get(self.request,
                                                  domain_id)
            for field in DOMAIN_INFO_FIELDS:
                initial[field] = getattr(domain_info, field, None)
        except:
            exceptions.handle(self.request,
                              _('Unable to retrieve domain details.'),
                              redirect=reverse(DOMAINS_INDEX_URL))
        return initial
