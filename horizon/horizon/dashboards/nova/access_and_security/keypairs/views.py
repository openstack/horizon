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
from horizon.dashboards.nova.access_and_security.keypairs.forms import \
                                  (CreateKeypair, DeleteKeypair, ImportKeypair)


LOG = logging.getLogger(__name__)


# FIXME(gabriel): There's a very obvious pattern to these views.
#                 This is a perfect candidate for a class-based view.

@login_required
def index(request):
    delete_form, handled = DeleteKeypair.maybe_handle(request)
    if handled:
        return handled

    try:
        keypairs = api.keypair_list(request)
    except novaclient_exceptions.ClientException, e:
        keypairs = []
        LOG.exception("ClientException in keypair index")
        messages.error(request, _('Error fetching keypairs: %s') % e.message)

    context = {'keypairs': keypairs, 'delete_form': delete_form}

    if request.is_ajax():
        template = 'nova/access_and_security/keypairs/_list.html'
        context['hide'] = True
    else:
        template = 'nova/access_and_security/keypairs/index.html'

    return shortcuts.render(request, template, context)


@login_required
def create(request):
    form, handled = CreateKeypair.maybe_handle(request)
    if handled:
        return handled

    context = {'form': form}

    if request.is_ajax():
        template = 'nova/access_and_security/keypairs/_create.html'
        context['hide'] = True
    else:
        template = 'nova/access_and_security/keypairs/create.html'

    return shortcuts.render(request, template, context)


@login_required
def import_keypair(request):
    form, handled = ImportKeypair.maybe_handle(request)
    if handled:
        return handled

    context = {'form': form}

    if request.is_ajax():
        template = 'nova/access_and_security/keypairs/_import.html'
        context['hide'] = True
    else:
        template = 'nova/access_and_security/keypairs/import.html'

    return shortcuts.render(request, template, context)
