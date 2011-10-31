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

import functools
import logging

from django.utils.decorators import available_attrs
import openstack.compute
import openstackx.admin
import openstackx.api.exceptions as openstackx_exceptions
import openstackx.extras

from horizon.api.base import *


LOG = logging.getLogger(__name__)


REBOOT_HARD = openstack.compute.servers.REBOOT_HARD


def check_openstackx(f):
    """Decorator that adds extra info to api exceptions

       The OpenStack Dashboard currently depends on openstackx extensions
       being present in Nova.  Error messages depending for views depending
       on these extensions do not lead to the conclusion that Nova is missing
       extensions.

       This decorator should be dropped and removed after Keystone and
       Horizon more gracefully handle extensions and openstackx extensions
       aren't required by Horizon in Nova.
    """
    @functools.wraps(f, assigned=available_attrs(f))
    def inner(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except openstackx_exceptions.NotFound, e:
            e.message = e.details or ''
            e.message += ' This error may be caused by a misconfigured' \
                         ' Nova url in keystone\'s service catalog, or ' \
                         ' by missing openstackx extensions in Nova. ' \
                         ' See the Horizon README.'
            raise
    return inner


def compute_api(request):
    management_url = url_for(request, 'compute')
    compute = openstack.compute.Compute(
        auth_token=request.user.token,
        management_url=management_url)
    # this below hack is necessary to make the jacobian compute client work
    # TODO(mgius): It looks like this is unused now?
    compute.client.auth_token = request.user.token
    compute.client.management_url = management_url
    LOG.debug('compute_api connection created using token "%s"'
                      ' and url "%s"' %
                      (request.user.token, management_url))
    return compute


def admin_api(request):
    management_url = url_for(request, 'compute', True)
    LOG.debug('admin_api connection created using token "%s"'
                    ' and url "%s"' %
                    (request.user.token, management_url))
    return openstackx.admin.Admin(auth_token=request.user.token,
                            management_url=management_url)


def extras_api(request):
    management_url = url_for(request, 'compute')
    LOG.debug('extras_api connection created using token "%s"'
                     ' and url "%s"' %
                    (request.user.token, management_url))
    return openstackx.extras.Extras(auth_token=request.user.token,
                                   management_url=management_url)
