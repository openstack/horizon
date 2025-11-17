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

from django.utils.translation import gettext_lazy as _

from horizon import exceptions
from horizon import forms
from horizon import messages

from openstack_dashboard import api


NEW_LINES = re.compile(r"\r|\n")

# NOTE: This name regex is used by the legacy (Django) key pair panel today.
# We reuse it for the de-angularized Generate form to keep validation consistent
# across Generate/Import, and to allow spaces (Nova supports them) while
# preventing whitespace-only names.
KEYPAIR_NAME_REGEX = re.compile(r"^\w+(?:[- ]\w+)*$", re.UNICODE)
KEYPAIR_ERROR_MESSAGES = {
    'invalid': _('Key pair name may only contain letters, '
                 'numbers, underscores, spaces, and hyphens '
                 'and may not be white space.')}


class GenerateKeyPairForm(forms.SelfHandlingForm):
    """Form for generating a new key pair (server-generated keys)."""

    name = forms.RegexField(
        max_length=255,
        label=_("Key Pair Name"),
        help_text=_("Name for the new key pair"),
        required=True,
        regex=KEYPAIR_NAME_REGEX,
        error_messages=KEYPAIR_ERROR_MESSAGES,
        widget=forms.TextInput(attrs={
            'placeholder': _('my-keypair'),
            'autofocus': 'autofocus'
        })
    )

    key_type = forms.ChoiceField(
        label=_("Key Type"),
        choices=[
            ('ssh', _('SSH Key')),
            ('x509', _('X509 Certificate'))
        ],
        initial='ssh',
        required=False,
        help_text=_("Type of key pair to generate (SSH is recommended)")
    )

    def handle(self, request, data):
        """Generate the key pair via Nova API."""
        try:
            # Call Nova API to generate key pair
            keypair = api.nova.keypair_create(
                request,
                data['name'],
                key_type=data.get('key_type', 'ssh')
            )

            self.keypair_private_key = getattr(keypair, 'private_key', None)
            self.keypair_name = keypair.name

            messages.success(
                request,
                _('Successfully created key pair "%(name)s". '
                  'Your private key is ready for download.') % {
                    'name': data['name']
                }
            )
            return True

        except Exception as e:
            exceptions.handle(
                request,
                _('Unable to create key pair: %s') % str(e)
            )
            return False


class ImportKeypair(forms.SelfHandlingForm):
    name = forms.RegexField(max_length=255,
                            label=_("Key Pair Name"),
                            regex=KEYPAIR_NAME_REGEX,
                            error_messages=KEYPAIR_ERROR_MESSAGES)
    key_type = forms.ChoiceField(label=_("Key Type"),
                                 widget=forms.SelectWidget(),
                                 choices=[('ssh', _("SSH Key")),
                                          ('x509', _("X509 Certificate"))],
                                 initial='ssh')
    public_key = forms.CharField(label=_("Public Key"),
                                 widget=forms.Textarea())

    def handle(self, request, data):
        try:
            # Remove any new lines in the ssh public key
            if data['key_type'] == 'ssh':
                data['public_key'] = NEW_LINES.sub("", data['public_key'])
            keypair = api.nova.keypair_import(request,
                                              data['name'],
                                              data['public_key'],
                                              data['key_type'])
            messages.success(request,
                             _('Successfully imported public key: %s')
                             % data['name'])
            return keypair
        except Exception:
            exceptions.handle(request, ignore=True)
            self.api_error(_('Unable to import key pair.'))
            return False
