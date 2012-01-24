# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright 2011 United States Government as represented by the
# Administrator of the National Aeronautics and Space Administration.
# All Rights Reserved.
#
# Copyright 2011 Nebula, Inc.
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
from django.contrib import messages

from horizon import api
from horizon import tables
from .tables import QuotasTable


LOG = logging.getLogger(__name__)


class IndexView(tables.DataTableView):
    table_class = QuotasTable
    template_name = 'syspanel/quotas/index.html'

    def get_data(self):
        try:
            quota_set = api.tenant_quota_defaults(self.request,
                                                  self.request.user.tenant_id)
            data = quota_set.items
        except Exception, e:
            data = []
            LOG.exception('Exception while getting quota info')
            messages.error(self.request,
                           _('Unable to get quota info: %s') % e)
        return data
