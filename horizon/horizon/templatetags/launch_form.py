# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright 2011 United States Government as represented by the
# Administrator of the National Aeronautics and Space Administration.
# All Rights Reserved.
#
# Copyright 2011 Openstack LLC
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
Template tags for dynamic creation of image launch form.
"""

from __future__ import absolute_import
import logging
from django import template
from openstackx.api import exceptions as api_exceptions
from novaclient import exceptions as novaclient_exceptions
from horizon import api
from horizon.dashboards.nova.images_and_snapshots.images.forms import \
                                                                     LaunchForm

from horizon.utils import assignment_tag

LOG = logging.getLogger(__name__)
register = template.Library()


@register.assignment_tag
def launch_form(request, tenant_id, image_id):

    def flavorlist(request):
        try:
            fl = api.flavor_list(request)

            # TODO add vcpu count to flavors
            sel = [(f.id, '%s (%svcpu / %sGB Disk / %sMB Ram )' %
                   (f.name, f.vcpus, f.disk, f.ram)) for f in fl]
            return sorted(sel)
        except api_exceptions.ApiException:
            LOG.exception('Unable to retrieve list of instance types')
            return [(1, 'm1.tiny')]

    def keynamelist(request):
        try:
            fl = api.keypair_list(request)
            sel = [(f.name, f.name) for f in fl]
            return sel
        except Exception:
            LOG.exception('Unable to retrieve list of keypairs')
            return []

    def securitygrouplist(request):
        try:
            fl = api.security_group_list(request)
            sel = [(f.name, f.name) for f in fl]
            return sel
        except novaclient_exceptions.ClientException:
            LOG.exception('Unable to retrieve list of security groups')
            return []

    form = LaunchForm(initial={'flavorlist': flavorlist(request),
                               'keynamelist': keynamelist(request),
                               'securitygrouplist': securitygrouplist(request),
                               'image_id': image_id,
                               'tenant_id': tenant_id})
    return form
