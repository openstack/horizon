# vim: tabstop=4 shiftwidth=4 softtabstop=4

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

""" Exceptions raised by the Horizon code. """


class NotAuthorized(Exception):
    """
    Raised whenever a user attempts to access a resource which they do not
    have role-based access to (such as when failing the
    :func:`~horizon.decorators.require_roles` decorator).

    The included :class:`~horizon.middleware.HorizonMiddleware` catches
    ``NotAuthorized`` and handles it gracefully by displaying an error
    message and redirecting the user to a login page.
    """
    pass


class ServiceCatalogException(Exception):
    """
    Raised when a requested service is not available in the ``ServiceCatalog``
    returned by Keystone.
    """
    def __init__(self, service_name):
        message = 'Invalid service catalog service: %s' % service_name
        super(ServiceCatalogException, self).__init__(message)
