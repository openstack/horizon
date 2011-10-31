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
Middleware provided and used by Horizon.
"""

from django.contrib import messages
from django import shortcuts
from django.utils.translation import ugettext as _

import openstackx
import openstack

from horizon import exceptions
from horizon import users


class HorizonMiddleware(object):
    """ The main Horizon middleware class. Required for use of Horizon. """

    def process_request(self, request):
        """ Adds data necessary for Horizon to function to the request.

        Adds the current "active" :class:`~horizon.Dashboard` and
        :class:`~horizon.Panel` to ``request.horizon``.

        Adds a :class:`~horizon.users.User` object to ``request.user``.
        """
        request.__class__.user = users.LazyUser()
        request.horizon = {'dashboard': None, 'panel': None}

    def process_exception(self, request, exception):
        """ Catch NotAuthorized and handle it gracefully. """
        if issubclass(exception.__class__, exceptions.NotAuthorized):
            messages.error(request, _(unicode(exception)))
            return shortcuts.redirect('/auth/logout')

        if type(exception) in [openstack.compute.exceptions.Forbidden,
                               openstackx.api.exceptions.Forbidden]:
            # flush other error messages, which are collateral damage
            # when our token expires
            for message in messages.get_messages(request):
                pass
            messages.error(request,
                           _('Your token has expired. Please log in again'))
            return shortcuts.redirect('/auth/logout')
