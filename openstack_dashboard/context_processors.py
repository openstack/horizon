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
from openstack_dashboard.contrib.developer.profiler import api as profiler


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
    if request.user.is_authenticated:
        context['authorized_tenants'] = [
            tenant for tenant in
            request.user.authorized_tenants if tenant.enabled]

    # Region context/support
    available_regions = settings.AVAILABLE_REGIONS
    regions = {'support': len(available_regions) > 1,
               'current': {'endpoint': request.session.get('region_endpoint'),
                           'name': request.session.get('region_name')},
               'available': [{'endpoint': region[0], 'name':region[1]} for
                             region in available_regions]}

    # K2K Federation Service Providers context/support
    available_providers = request.session.get('keystone_providers', [])
    if available_providers:
        provider_id = request.session.get('keystone_provider_id', None)
        provider_name = None
        for provider in available_providers:
            if provider['id'] == provider_id:
                provider_name = provider.get('name')

        keystone_providers = {
            'support': len(available_providers) > 1,
            'current': {
                'name': provider_name,
                'id': provider_id
            },
            'available': [
                {'name': keystone_provider['name'],
                 'id': keystone_provider['id']}
                for keystone_provider in available_providers]
        }
    else:
        keystone_providers = {'support': False}

    context['keystone_providers'] = keystone_providers
    context['regions'] = regions

    # Adding webroot access
    context['WEBROOT'] = settings.WEBROOT

    context['USER_MENU_LINKS'] = settings.USER_MENU_LINKS
    context['LOGOUT_URL'] = settings.LOGOUT_URL

    # Adding profiler support flag
    profiler_settings = settings.OPENSTACK_PROFILER
    profiler_enabled = profiler_settings['enabled']
    context['profiler_enabled'] = profiler_enabled
    if profiler_enabled and 'profile_page' in request.COOKIES:
        index_view_id = request.META.get(profiler.ROOT_HEADER, '')
        hmac_keys = profiler_settings['keys']
        context['x_trace_info'] = profiler.update_trace_headers(
            hmac_keys, parent_id=index_view_id)

    context['JS_CATALOG'] = get_js_catalog(conf)

    return context


def get_js_catalog(conf):
    # Search for external plugins and append to javascript message catalog
    # internal plugins are under the openstack_dashboard domain
    # so we exclude them from the js_catalog
    js_catalog = ['horizon', 'openstack_dashboard']
    regex = re.compile(r'^openstack_dashboard')
    all_plugins = conf.HORIZON_CONFIG.get('plugins', [])
    js_catalog.extend(p for p in all_plugins if not regex.search(p))
    return '+'.join(js_catalog)
