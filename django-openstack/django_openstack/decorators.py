# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright 2011 United States Government as represented by the
# Administrator of the National Aeronautics and Space Administration.
# All Rights Reserved.
#
# Copyright 2011 CRS4
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
Simple decorator container for general purpose
"""

from django.shortcuts import redirect
import logging


LOG = logging.getLogger('django_openstack.syspanel')


def enforce_admin_access(fn):
    """ Preserve unauthorized bypass typing directly the URL and redirects to
    the overview dash page """
    def dec(*args, **kwargs):
        if args[0].user.is_admin():
            return fn(*args, **kwargs)
        else:
            LOG.warn('Redirecting user "%s" from syspanel to dash  ( %s )' %
                     (args[0].user.username, fn.__name__))
            return redirect('dash_overview')
    return dec
