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
Views for managing Nova keypairs.
"""
import logging

from django import http
from django import shortcuts
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.utils.translation import ugettext as _
from novaclient import exceptions as novaclient_exceptions

from horizon import api
from horizon.dashboards.nova.keypairs.forms import (CreateKeypair,
        DeleteKeypair, ImportKeypair)


LOG = logging.getLogger(__name__)


@login_required
def index(request):
    delete_form, handled = DeleteKeypair.maybe_handle(request)

    if handled:
        return handled

    create_form = CreateKeypair()
    import_form = ImportKeypair()

    try:
        keypairs = api.keypair_list(request)
    except novaclient_exceptions.ClientException, e:
        keypairs = []
        LOG.exception("ClientException in keypair index")
        messages.error(request, _('Error fetching keypairs: %s') % e.message)

    return shortcuts.render(request,
                            'nova/keypairs/index.html', {
                                'keypairs': keypairs,
                                'create_form': create_form,
                                'import_form': import_form,
                                'delete_form': delete_form})


@login_required
def create(request):
    form, handled = CreateKeypair.maybe_handle(request)
    if handled:
        return handled

    return shortcuts.render(request,
                            'nova/keypairs/create.html', {
                                'create_form': form})


@login_required
def import_keypair(request):
    form, handled = ImportKeypair.maybe_handle(request)
    if handled:
        return handled

    return shortcuts.render(request,
                            'nova/keypairs/import.html', {
                                'import_form': form,
                                'create_form': form})
