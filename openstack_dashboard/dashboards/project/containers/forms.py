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

import logging

from django.core import validators
from django.core.urlresolvers import reverse
from django.utils.translation import ugettext_lazy as _

from horizon import exceptions
from horizon import forms
from horizon import messages

from openstack_dashboard import api
from .tables import wrap_delimiter


LOG = logging.getLogger(__name__)


no_slash_validator = validators.RegexValidator(r'^(?u)[^/]+$',
                                               _("Slash is not an allowed "
                                                 "character."),
                                               code="noslash")


class CreateContainer(forms.SelfHandlingForm):
    parent = forms.CharField(max_length=255,
                             required=False,
                             widget=forms.HiddenInput)
    name = forms.CharField(max_length=255,
                           label=_("Container Name"),
                           validators=[no_slash_validator])

    def handle(self, request, data):
        try:
            if not data['parent']:
                # Create a container
                api.swift.swift_create_container(request, data["name"])
                messages.success(request, _("Container created successfully."))
            else:
                # Create a pseudo-folder
                container, slash, remainder = data['parent'].partition("/")
                remainder = remainder.rstrip("/")
                subfolder_name = "/".join([bit for bit
                                           in (remainder, data['name'])
                                           if bit])
                api.swift.swift_create_subfolder(request,
                                                 container,
                                                 subfolder_name)
                messages.success(request, _("Folder created successfully."))
            return True
        except:
            exceptions.handle(request, _('Unable to create container.'))


class UploadObject(forms.SelfHandlingForm):
    path = forms.CharField(max_length=255,
                           required=False,
                           widget=forms.HiddenInput)
    name = forms.CharField(max_length=255,
                           label=_("Object Name"),
                           help_text=_("Slashes are allowed, and are treated "
                                       "as pseudo-folders by the Object "
                                       "Store."))
    object_file = forms.FileField(label=_("File"), allow_empty_file=True)
    container_name = forms.CharField(widget=forms.HiddenInput())

    def handle(self, request, data):
        object_file = self.files['object_file']
        if data['path']:
            object_path = "/".join([data['path'].rstrip("/"), data['name']])
        else:
            object_path = data['name']
        try:
            obj = api.swift.swift_upload_object(request,
                                                data['container_name'],
                                                object_path,
                                                object_file)
            messages.success(request, _("Object was successfully uploaded."))
            return obj
        except:
            exceptions.handle(request, _("Unable to upload object."))


class CopyObject(forms.SelfHandlingForm):
    new_container_name = forms.ChoiceField(label=_("Destination container"),
                                           validators=[no_slash_validator])
    path = forms.CharField(max_length=255, required=False)
    new_object_name = forms.CharField(max_length=255,
                                      label=_("Destination object name"),
                                      validators=[no_slash_validator])
    orig_container_name = forms.CharField(widget=forms.HiddenInput())
    orig_object_name = forms.CharField(widget=forms.HiddenInput())

    def __init__(self, *args, **kwargs):
        containers = kwargs.pop('containers')
        super(CopyObject, self).__init__(*args, **kwargs)
        self.fields['new_container_name'].choices = containers

    def handle(self, request, data):
        index = "horizon:project:containers:index"
        orig_container = data['orig_container_name']
        orig_object = data['orig_object_name']
        new_container = data['new_container_name']
        new_object = data['new_object_name']
        path = data['path']
        if path and not path.endswith("/"):
            path = path + "/"
        new_path = "%s%s" % (path, new_object)

        # Now copy the object itself.
        try:
            api.swift.swift_copy_object(request,
                                        orig_container,
                                        orig_object,
                                        new_container,
                                        new_path)
            dest = "%s/%s" % (new_container, path)
            vals = {"dest": dest.rstrip("/"),
                    "orig": orig_object.split("/")[-1],
                    "new": new_object}
            messages.success(request,
                             _('Copied "%(orig)s" to "%(dest)s" as "%(new)s".')
                             % vals)
            return True
        except exceptions.HorizonException, exc:
            messages.error(request, exc)
            raise exceptions.Http302(reverse(index,
                                     args=[wrap_delimiter(orig_container)]))
        except:
            redirect = reverse(index, args=[wrap_delimiter(orig_container)])
            exceptions.handle(request,
                              _("Unable to copy object."),
                              redirect=redirect)
