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
from django.contrib.auth.decorators import login_required

from horizon import api


LOG = logging.getLogger(__name__)


@login_required
def index(request):
    try:
        quotas = api.admin_api(request).quota_sets.get(True)._info
        quotas['ram'] = int(quotas['ram']) / 100
        quotas.pop('id')
    except Exception, e:
        quotas = None
        LOG.exception('Exception while getting quota info')
        if not hasattr(e, 'message'):
            e.message = str(e)
        messages.error(request, _('Unable to get quota info: %s') % e.message)

    return shortcuts.render(request,
                            'syspanel/quotas/index.html', {
                                'quotas': quotas})
