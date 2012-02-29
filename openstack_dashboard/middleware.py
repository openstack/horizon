# vim: tabstop=4 shiftwidth=4 softtabstop=4

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

import logging

from django import shortcuts
from django.contrib import messages
from novaclient import exceptions as novaclient_exceptions


LOG = logging.getLogger('openstack_dashboard')


class DashboardLogUnhandledExceptionsMiddleware(object):
    def process_exception(self, request, exception):
        if isinstance(exception, novaclient_exceptions.Unauthorized):
            try:
                exception.message.index('reauthenticate')
                # clear the errors
                for message in messages.get_messages(request):
                    LOG.debug('Discarded message - %s: "%s"'
                              % (message.tags, message.message))
                messages.info(request, 'Your session has timed out.'
                                       ' Please log back in.')
                LOG.info('User "%s" auth token expired, redirecting to logout'
                         % request.user.username)
                return shortcuts.redirect('auth_logout')

            except ValueError:
                pass

        LOG.critical('Unhandled Exception in of type "%s" in dashboard.'
                     % type(exception), exc_info=True)
