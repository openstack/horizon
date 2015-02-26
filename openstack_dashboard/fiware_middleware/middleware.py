# Copyright (C) 2014 Universidad Politecnica de Madrid
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

import logging

from django import http
from django.conf import settings
from django.core.urlresolvers import reverse

from horizon.utils import functions as utils

from keystoneclient.openstack.common.apiclient \
    import exceptions as kc_exceptions

from openstack_dashboard import api
from openstack_dashboard import fiware_api


LOG = logging.getLogger('idm_logger')

# TODO(garcianavalon) all the logout and unauthorized stuff could go
# into its own middleware

class UserInfoMiddleware(object):
    """Adds more user info to the request object for convenience."""

    def process_request(self, request):
        if (reverse('logout') == request.META['PATH_INFO']
            or not hasattr(request, 'user') 
            or not request.user.is_authenticated()):
            return
        try:
            user_data = api.keystone.user_get(request, request.user.id)
            # setattr(user_data, 'username', user_data.name)
            for attr, value in user_data.__dict__.iteritems():
                setattr(request.user, attr, value)
        except kc_exceptions.Unauthorized:
            response = http.HttpResponseRedirect(settings.LOGOUT_URL)
            msg = ("Session expired")
            LOG.info(msg)
            utils.add_logout_reason(request, response, msg)
            return response
        

class OrganizationInfoMiddleware(object):
    """Adds organization info to the request object for convenience."""

    def process_request(self, request):
        if (reverse('logout') == request.META['PATH_INFO']
            or not hasattr(request, 'user') 
            or not request.user.is_authenticated()):
            return
        current_organization = request.user.token.project['id']

        # TODO(garcianavalon) lazyloading and caching
        request.organization = api.keystone.tenant_get(
            request, current_organization)


class SwitchMiddleware(object):
    """Adds all the possible organizations the user can switch to."""

    def process_request(self, request):
        # Allowed if he is an admin in the organization
        if (reverse('logout') == request.META['PATH_INFO']
            or not hasattr(request, 'user')
            or not request.user.is_authenticated()
            or not hasattr(request, 'organization')):
            return

        # TODO(garcianavalon) lazyloading and caching
        # TODO(garcianavalon) move to fiware_api
        organizations, more = api.keystone.tenant_list(request)
        assignments = api.keystone.role_assignments_list(
            request, user=request.user.id)
        owner_role = fiware_api.keystone.get_owner_role(request)
        switch_orgs = set([a.scope['project']['id'] for a in assignments 
                       if a.role['id'] == owner_role.id
                       and a.scope['project']['id'] != request.organization.id])
        request.organizations = [org for org in organizations
                                 if org.id in switch_orgs]