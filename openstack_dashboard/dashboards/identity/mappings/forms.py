# Copyright (C) 2015 Yahoo! Inc. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

import json

from django.utils.translation import ugettext_lazy as _

from horizon import exceptions
from horizon import forms
from horizon import messages

from openstack_dashboard import api


class CreateMappingForm(forms.SelfHandlingForm):
    id = forms.CharField(label=_("Mapping ID"),
                         max_length=64,
                         help_text=_("User-defined unique id to identify "
                                     "the mapping."))
    rules = forms.CharField(label=_("Rules"),
                            widget=forms.widgets.Textarea(attrs={'rows': 4}),
                            help_text=_("Set of rules to map federation "
                                        "protocol attributes to Identity "
                                        "API objects."))

    def handle(self, request, data):
        try:
            rules = json.loads(data["rules"])
            new_mapping = api.keystone.mapping_create(
                request,
                data["id"],
                rules=rules)
            messages.success(request,
                             _("Mapping created successfully."))
            return new_mapping
        except exceptions.Conflict:
            msg = _('Mapping ID "%s" is already used.') % data["id"]
            messages.error(request, msg)
        except (TypeError, ValueError):
            msg = _("Unable to create mapping. Rules has malformed JSON data.")
            messages.error(request, msg)
        except Exception:
            exceptions.handle(request,
                              _("Unable to create mapping."))
        return False


class UpdateMappingForm(forms.SelfHandlingForm):
    id = forms.CharField(label=_("Mapping ID"),
                         widget=forms.TextInput(
                             attrs={'readonly': 'readonly'}),
                         help_text=_("User-defined unique id to "
                                     "identify the mapping."))
    rules = forms.CharField(label=_("Rules"),
                            widget=forms.widgets.Textarea(attrs={'rows': 4}),
                            help_text=_("Set of rules to map federation "
                                        "protocol attributes to Identity "
                                        "API objects."))

    def handle(self, request, data):
        try:
            rules = json.loads(data["rules"])
            api.keystone.mapping_update(
                request,
                data['id'],
                rules=rules)
            messages.success(request,
                             _("Mapping updated successfully."))
            return True
        except (TypeError, ValueError):
            msg = _("Unable to update mapping. Rules has malformed JSON data.")
            messages.error(request, msg)
        except Exception:
            exceptions.handle(request,
                              _('Unable to update mapping.'))
