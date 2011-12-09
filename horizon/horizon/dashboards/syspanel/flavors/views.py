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
from django.utils.translation import ugettext as _
from novaclient import exceptions as api_exceptions

from horizon import api
from horizon import forms
from horizon.dashboards.syspanel.flavors.forms import (CreateFlavor,
        DeleteFlavor)
from horizon.dashboards.syspanel.instances import views as instance_views


LOG = logging.getLogger(__name__)


@login_required
def index(request):
    for f in (DeleteFlavor,):
        form, handled = f.maybe_handle(request)
        if handled:
            return handled

    delete_form = DeleteFlavor()

    flavors = []
    try:
        flavors = api.flavor_list(request)
    except api_exceptions.Unauthorized, e:
        LOG.exception('Unauthorized attempt to access flavor list.')
        messages.error(request, _('Unauthorized.'))
    except Exception, e:
        LOG.exception('Exception while fetching usage info')
        messages.error(request, _('Unable to get flavor list: %s') % e.message)

    flavors.sort(key=lambda x: x.id, reverse=True)
    return shortcuts.render(request,
                            'syspanel/flavors/index.html', {
                                'delete_form': delete_form,
                                'flavors': flavors})


@login_required
def create(request):
    form, handled = CreateFlavor.maybe_handle(request)
    if handled:
        return handled

    global_summary = instance_views.GlobalSummary(request)
    global_summary.service()
    global_summary.avail()
    global_summary.human_readable('disk_size')
    global_summary.human_readable('ram_size')

    return shortcuts.render(request,
                            'syspanel/flavors/create.html', {
                                'global_summary': global_summary.summary,
                                'form': form})
