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
"""
Context processors used by Horizon.
"""

import logging

from django.conf import settings

from horizon import api


LOG = logging.getLogger(__name__)


def horizon(request):
    """ The main Horizon context processor. Required for Horizon to function.

    Adds three variables to the request context:

    ``authorized_tenants``
        A list of tenant objects which the current user has access to.

    ``object_store_configured``
        Boolean. Will be ``True`` if there is a service of type
        ``object-store`` in the user's ``ServiceCatalog``.

    ``network_configured``
        Boolean. Will be ``True`` if ``settings.QUANTUM_ENABLED`` is ``True``.

    Additionally, it sets the names ``True`` and ``False`` in the context
    to their boolean equivalents for convenience.

    .. warning::

        Don't put API calls in context processors; they will be called once
        for each template/template fragment which takes context that is used
        to render the complete output.
    """
    context = {"True": True,
               "False": False}

    # Auth/Keystone context
    context.setdefault('authorized_tenants', [])
    if request.user.is_authenticated():
        context['authorized_tenants'] = request.user.authorized_tenants

    # Object Store/Swift context
    catalog = getattr(request.user, 'service_catalog', [])
    object_store = catalog and api.get_service_from_catalog(catalog,
                                                            'object-store')
    context['object_store_configured'] = object_store

    # Quantum context
    # TODO(gabriel): Convert to service catalog check when Quantum starts
    #                supporting keystone integration.
    context['network_configured'] = getattr(settings, 'QUANTUM_ENABLED', None)

    # Region context/support
    available_regions = getattr(settings, 'AVAILABLE_REGIONS', None)
    regions = {'support': available_regions > 1,
               'endpoint': request.session.get('region_endpoint'),
               'name': request.session.get('region_name')}
    context['region'] = regions

    return context
