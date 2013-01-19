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

import re

from django.core import validators
from django.utils.translation import ugettext_lazy as _

from horizon import exceptions
from horizon import forms
from horizon import messages

from openstack_dashboard import api


NEW_LINES = re.compile(r"\r|\n")


class CreateKeypair(forms.SelfHandlingForm):
    name = forms.CharField(max_length="20",
                           label=_("Keypair Name"),
                           validators=[validators.validate_slug],
                           error_messages={'invalid': _('Keypair names may '
                                'only contain letters, numbers, underscores '
                                'and hyphens.')})

    def handle(self, request, data):
        return True  # We just redirect to the download view.


class ImportKeypair(forms.SelfHandlingForm):
    name = forms.CharField(max_length="20", label=_("Keypair Name"),
                 validators=[validators.RegexValidator('\w+')])
    public_key = forms.CharField(label=_("Public Key"), widget=forms.Textarea)

    def handle(self, request, data):
        try:
            # Remove any new lines in the public key
            data['public_key'] = NEW_LINES.sub("", data['public_key'])
            keypair = api.nova.keypair_import(request,
                                              data['name'],
                                              data['public_key'])
            messages.success(request, _('Successfully imported public key: %s')
                                       % data['name'])
            return keypair
        except:
            exceptions.handle(request, ignore=True)
            self.api_error(_('Unable to import keypair.'))
            return False
