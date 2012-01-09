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

import logging

from django import http
from django import shortcuts
from django.contrib import messages
from django.core import validators
from django.template.defaultfilters import slugify
from django.utils.http import urlquote
from django.utils.translation import ugettext as _
from novaclient import exceptions as novaclient_exceptions

from horizon import api
from horizon import forms


LOG = logging.getLogger(__name__)


class CreateKeypair(forms.SelfHandlingForm):
    name = forms.CharField(max_length="20",
                           label=_("Keypair Name"),
                           validators=[validators.validate_slug],
                           error_messages={'invalid': _('Keypair names may '
                                'only contain letters, numbers, underscores '
                                'and hyphens.')})

    def handle(self, request, data):
        try:
            LOG.info('Creating keypair "%s"' % data['name'])
            keypair = api.keypair_create(request, data['name'])
            response = http.HttpResponse(mimetype='application/binary')
            response['Content-Disposition'] = \
                     'attachment; filename=%s.pem' % slugify(keypair.name)
            response.write(keypair.private_key)
            response['Content-Length'] = str(len(response.content))
            return response
        except novaclient_exceptions.ClientException, e:
            LOG.exception("ClientException in CreateKeyPair")
            messages.error(request,
                           _('Error Creating Keypair: %s') % e.message)
            return shortcuts.redirect(request.build_absolute_uri())


class ImportKeypair(forms.SelfHandlingForm):
    name = forms.CharField(max_length="20", label=_("Keypair Name"),
                 validators=[validators.RegexValidator('\w+')])
    public_key = forms.CharField(label=_("Public Key"), widget=forms.Textarea)

    def handle(self, request, data):
        try:
            LOG.info('Importing keypair "%s"' % data['name'])
            api.keypair_import(request, data['name'], data['public_key'])
            messages.success(request, _('Successfully imported public key: %s')
                                       % data['name'])
            return shortcuts.redirect(
                            'horizon:nova:access_and_security:index')
        except novaclient_exceptions.ClientException, e:
            LOG.exception("ClientException in ImportKeypair")
            messages.error(request,
                           _('Error Importing Keypair: %s') % e.message)
            return shortcuts.redirect(request.build_absolute_uri())
