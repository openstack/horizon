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
Views for managing Swift containers.
"""
import logging

from django import template
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django import shortcuts
from django.utils.translation import ugettext as _

from django_openstack import api
from django_openstack import forms

from cloudfiles.errors import ContainerNotEmpty


LOG = logging.getLogger('django_openstack.dash')


class DeleteContainer(forms.SelfHandlingForm):
    container_name = forms.CharField(widget=forms.HiddenInput())

    def handle(self, request, data):
        try:
            api.swift_delete_container(request, data['container_name'])
        except ContainerNotEmpty, e:
            messages.error(request,
                           _('Unable to delete non-empty container: %s') %
                           data['container_name'])
            LOG.exception('Unable to delete container "%s".  Exception: "%s"' %
                      (data['container_name'], str(e)))
        else:
            messages.info(request,
                      _('Successfully deleted container: %s') % \
                      data['container_name'])
        return shortcuts.redirect(request.build_absolute_uri())


class CreateContainer(forms.SelfHandlingForm):
    name = forms.CharField(max_length="255", label=_("Container Name"))

    def handle(self, request, data):
        api.swift_create_container(request, data['name'])
        messages.success(request, _("Container was successfully created."))
        return shortcuts.redirect("dash_containers", request.user.tenant_id)


@login_required
def index(request, tenant_id):
    marker = request.GET.get('marker', None)

    delete_form, handled = DeleteContainer.maybe_handle(request)
    if handled:
        return handled

    containers = api.swift_get_containers(request, marker=marker)

    return shortcuts.render_to_response(
    'django_openstack/dash/containers/index.html', {
        'containers': containers,
        'delete_form': delete_form,
    }, context_instance=template.RequestContext(request))


@login_required
def create(request, tenant_id):
    form, handled = CreateContainer.maybe_handle(request)
    if handled:
        return handled

    return shortcuts.render_to_response(
    'django_openstack/dash/containers/create.html', {
        'create_form': form,
    }, context_instance=template.RequestContext(request))
