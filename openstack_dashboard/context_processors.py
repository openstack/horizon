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
"""
Context processors used by Horizon.
"""

import re

from django.conf import settings

from horizon import conf


def openstack(request):
    """Context processor necessary for OpenStack Dashboard functionality.

    The following variables are added to the request context:

    ``authorized_tenants``
        A list of tenant objects which the current user has access to.

    ``regions``

        A dictionary containing information about region support, the current
        region, and available regions.
    """
    context = {}

    # Auth/Keystone context
    context.setdefault('authorized_tenants', [])
    if request.user.is_authenticated():
        context['authorized_tenants'] = [
            tenant for tenant in
            request.user.authorized_tenants if tenant.enabled]

    # Region context/support
    available_regions = getattr(settings, 'AVAILABLE_REGIONS', [])
    regions = {'support': len(available_regions) > 1,
               'current': {'endpoint': request.session.get('region_endpoint'),
                           'name': request.session.get('region_name')},
               'available': [{'endpoint': region[0], 'name':region[1]} for
                             region in available_regions]}
    context['regions'] = regions

    # Adding webroot access
    context['WEBROOT'] = getattr(settings, "WEBROOT", "/")

    # Search for external plugins and append to javascript message catalog
    # internal plugins are under the openstack_dashboard domain
    # so we exclude them from the js_catalog
    js_catalog = ['horizon', 'openstack_dashboard']
    regex = re.compile(r'^openstack_dashboard')
    all_plugins = conf.HORIZON_CONFIG['plugins']
    js_catalog.extend(p for p in all_plugins if not regex.search(p))
    context['JS_CATALOG'] = '+'.join(js_catalog)

    return context
