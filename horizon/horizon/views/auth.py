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
from django.conf import settings
from django.utils.translation import ugettext as _

import horizon
from horizon import api
from horizon import exceptions
from horizon import users
from horizon.base import Horizon
from horizon.views.auth_forms import Login, LoginWithTenant, _set_session_data


LOG = logging.getLogger(__name__)


def user_home(request):
    """ Reversible named view to direct a user to the appropriate homepage. """
    return shortcuts.redirect(horizon.get_user_home(request.user))


def login(request):
    """
    Logs in a user and redirects them to the URL specified by
    :func:`horizon.get_user_home`.
    """
    if request.user.is_authenticated():
        user = users.User(users.get_user_from_request(request))
        return shortcuts.redirect(Horizon.get_user_home(user))

    form, handled = Login.maybe_handle(request)
    if handled:
        return handled

    # FIXME(gabriel): we don't ship a template named splash.html
    return shortcuts.render(request, 'splash.html', {'form': form})


def switch_tenants(request, tenant_id):
    """
    Swaps a user from one tenant to another using the unscoped token from
    Keystone to exchange scoped tokens for the new tenant.
    """
    form, handled = LoginWithTenant.maybe_handle(
            request, initial={'tenant': tenant_id,
                              'username': request.user.username})
    if handled:
        return handled

    unscoped_token = request.session.get('unscoped_token', None)
    if unscoped_token:
        try:
            token = api.token_create_scoped(request,
                                            tenant_id,
                                            unscoped_token)
            _set_session_data(request, token)
            user = users.User(users.get_user_from_request(request))
            return shortcuts.redirect(Horizon.get_user_home(user))
        except Exception, e:
            exceptions.handle(request,
                              _("You are not authorized for that tenant."))

    return shortcuts.redirect("horizon:auth_login")


def logout(request):
    """ Clears the session and logs the current user out. """
    request.session.clear()
    # FIXME(gabriel): we don't ship a view named splash
    return shortcuts.redirect('splash')
