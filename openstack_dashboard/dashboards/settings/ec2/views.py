# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright 2012 Openstack, LLC
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

from horizon import forms

from .forms import DownloadX509Credentials


LOG = logging.getLogger(__name__)


class IndexView(forms.ModalFormView):
    form_class = DownloadX509Credentials
    template_name = 'settings/ec2/index.html'

    def form_valid(self, form):
        return form.handle(self.request, form.cleaned_data)
