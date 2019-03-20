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

from django.utils.translation import ugettext_lazy as _

from horizon import exceptions
from horizon import forms
from horizon import messages

from openstack_dashboard import api


NEW_LINES = re.compile(r"\r|\n")

KEYPAIR_NAME_REGEX = re.compile(r"^\w+(?:[- ]\w+)*$", re.UNICODE)
KEYPAIR_ERROR_MESSAGES = {
    'invalid': _('Key pair name may only contain letters, '
                 'numbers, underscores, spaces, and hyphens '
                 'and may not be white space.')}


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
