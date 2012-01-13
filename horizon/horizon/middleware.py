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
        """ Catch NotAuthorized and Http302 and handle them gracefully. """
        if isinstance(exception, exceptions.NotAuthorized):
            messages.error(request, unicode(exception))
            return shortcuts.redirect('/auth/login')

        if isinstance(exception, exceptions.Http302):
            return shortcuts.redirect(exception.location)
