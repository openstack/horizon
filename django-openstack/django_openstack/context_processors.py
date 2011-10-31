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

from django.conf import settings
from django_openstack import api
from django.contrib import messages
from openstackx.api import exceptions as api_exceptions


def tenants(request):
    if not request.user or not request.user.is_authenticated():
        return {}

    try:
        return {'tenants': api.tenant_list_for_token(request,
                                                     request.user.token)}
    except api_exceptions.BadRequest, e:
        messages.error(request, _("Unable to retrieve tenant list from\
                                  keystone: %s") % e.message)
        return {'tenants': []}


def object_store(request):
    catalog = getattr(request.user, 'service_catalog', [])
    object_store = catalog and api.get_service_from_catalog(catalog,
                                                            'object-store')
    return {'object_store_configured': object_store}


def quantum(request):
    return {'quantum_configured': settings.QUANTUM_ENABLED}
