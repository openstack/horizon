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

from horizon import forms
from .forms import CreateKeypair, ImportKeypair


LOG = logging.getLogger(__name__)


class CreateView(forms.ModalFormView):
    form_class = CreateKeypair
    template_name = 'nova/access_and_security/keypairs/create.html'


class ImportView(forms.ModalFormView):
    form_class = ImportKeypair
    template_name = 'nova/access_and_security/keypairs/import.html'
