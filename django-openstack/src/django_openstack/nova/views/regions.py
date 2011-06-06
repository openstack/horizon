# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright 2010 United States Government as represented by the
# Administrator of the National Aeronautics and Space Administration.
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

"""
Views for managing Nova regions.
"""

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect
from django.utils.translation import ugettext as _
from django_openstack import log as logging
from django_openstack.nova.shortcuts import set_current_region


LOG = logging.getLogger('django_openstack.nova')


@login_required
def change(request):
    region = request.POST['region']
    redirect_url = request.POST['redirect_url']
    set_current_region(request, region)
    messages.success(request, _('You are now using the region "%s".') % region)
    LOG.info('User "%s" changed to region "%s"' % (str(request.user), region))
    return redirect(redirect_url)
