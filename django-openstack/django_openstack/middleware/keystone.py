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

from django.contrib import messages
from django import shortcuts
from django.utils.translation import ugettext as _

import openstackx
import openstack


class User(object):
    def __init__(self, token=None, user=None, tenant_id=None, admin=None,
                    service_catalog=None, tenant_name=None):
        self.token = token
        self.username = user
        self.tenant_id = tenant_id
        self.tenant_name = tenant_name
        self.admin = admin
        self.service_catalog = service_catalog

    def is_authenticated(self):
        # TODO: deal with token expiration
        return self.token

    def is_admin(self):
        return self.admin


def get_user_from_request(request):
    if 'user' not in request.session:
        return User()
    return User(token=request.session['token'],
                user=request.session['user'],
                tenant_id=request.session['tenant_id'],
                tenant_name=request.session['tenant'],
                admin=request.session['admin'],
                service_catalog=request.session['serviceCatalog'])


class LazyUser(object):
    def __get__(self, request, obj_type=None):
        if not hasattr(request, '_cached_user'):
            request._cached_user = get_user_from_request(request)
        return request._cached_user


class AuthenticationMiddleware(object):
    def process_request(self, request):
        request.__class__.user = LazyUser()

    def process_exception(self, request, exception):
        if type(exception) in [openstack.compute.exceptions.Forbidden,
                               openstackx.api.exceptions.Forbidden]:
            # flush other error messages, which are collateral damage
            # when our token expires
            for message in messages.get_messages(request):
                pass
            messages.error(request,
                           _('Your token has expired. Please log in again'))
            return shortcuts.redirect('/auth/logout')
