# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright 2013 Reliance Jio Infocomm, Ltd.
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

from django.forms.forms import NON_FIELD_ERRORS
from horizon import forms


class ContribSelfHandlingForm(forms.SelfHandlingForm):

    def __init__(self, request, *args, **kwargs):
        super(ContribSelfHandlingForm, self).__init__(request, *args, **kwargs)	

    def set_non_field_errors(self, error_list):
        #set non field errors, so we can show that in ui.
        try:
            self._errors[NON_FIELD_ERRORS].append(self.error_class(error_list))
        except KeyError:
            self._errors[NON_FIELD_ERRORS] = self.error_class(error_list)

    def get_default_error_message(self):
        return "Unable to process your request.\
                Please contact the site administrator"