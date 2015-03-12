# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
# implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import logging
import uuid

from django.forms import util
from django.forms import widgets
from django import template
from django.template import defaultfilters
from django.utils.encoding import force_text
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext_lazy as _

from horizon import exceptions
from horizon import forms
from horizon import messages

from openstack_dashboard.api import sahara as saharaclient

LOG = logging.getLogger(__name__)


class LabeledInput(widgets.Input):
    def render(self, name, values, attrs=None):
        final_attrs = self.build_attrs(attrs, type=self.input_type, name=name)
        output = "<span id='%s'>%s</span>%s" %\
            ("id_%s_label" % name,
             "swift://",
             ('<input%s />' % util.flatatt(final_attrs)))
        return mark_safe(output)


class JobBinaryCreateForm(forms.SelfHandlingForm):
    NEW_SCRIPT = "newscript"
    UPLOAD_BIN = "uploadfile"

    job_binary_name = forms.CharField(label=_("Name"))

    job_binary_type = forms.ChoiceField(
        label=_("Storage type"),
        widget=forms.Select(
            attrs={
                'class': 'switchable',
                'data-slug': 'jb_type'
            }))

    job_binary_url = forms.CharField(
        label=_("URL"),
        required=False,
        widget=LabeledInput(
            attrs={
                'class': 'switched',
                'data-switch-on': 'jb_type',
                'data-jb_type-swift': _('URL')
            }))

    job_binary_internal = forms.ChoiceField(
        label=_("Internal binary"),
        required=False,
        widget=forms.Select(
            attrs={
                'class': 'switched switchable',
                'data-slug': 'jb_internal',
                'data-switch-on': 'jb_type',
                'data-jb_type-internal-db': _('Internal Binary')
            }))

    job_binary_file = forms.FileField(
        label=_("Upload File"),
        required=False,
        widget=forms.ClearableFileInput(
            attrs={
                'class': 'switched',
                'data-switch-on': 'jb_internal',
                'data-jb_internal-uploadfile': _("Upload File")
            }))

    job_binary_script_name = forms.CharField(
        label=_("Script name"),
        required=False,
        widget=forms.TextInput(
            attrs={
                'class': 'switched',
                'data-switch-on': 'jb_internal',
                'data-jb_internal-newscript': _("Script name")
            }))

    job_binary_script = forms.CharField(
        label=_("Script text"),
        required=False,
        widget=forms.Textarea(
            attrs={
                'rows': 4,
                'class': 'switched',
                'data-switch-on': 'jb_internal',
                'data-jb_internal-newscript': _("Script text")
            }))

    job_binary_username = forms.CharField(
        label=_("Username"),
        required=False,
        widget=forms.TextInput(
            attrs={
                'class': 'switched',
                'data-switch-on': 'jb_type',
                'data-jb_type-swift': _('Username')
            }))

    job_binary_password = forms.CharField(
        label=_("Password"),
        required=False,
        widget=forms.PasswordInput(
            attrs={
                'autocomplete': 'off',
                'class': 'switched',
                'data-switch-on': 'jb_type',
                'data-jb_type-swift': _('Password')
            }))

    job_binary_description = forms.CharField(label=_("Description"),
                                             required=False,
                                             widget=forms.Textarea())

    def __init__(self, request, *args, **kwargs):
        super(JobBinaryCreateForm, self).__init__(request, *args, **kwargs)

        self.help_text_template = ("project/data_processing.job_binaries/"
                                   "_create_job_binary_help.html")

        self.fields["job_binary_type"].choices =\
            [("internal-db", "Internal database"),
             ("swift", "Swift")]

        self.fields["job_binary_internal"].choices =\
            self.populate_job_binary_internal_choices(request)

    def populate_job_binary_internal_choices(self, request):
        try:
            job_binaries = saharaclient.job_binary_internal_list(request)
        except Exception:
            exceptions.handle(request,
                              _("Failed to get list of internal binaries."))
            job_binaries = []

        choices = [(job_binary.id, job_binary.name)
                   for job_binary in job_binaries]
        choices.insert(0, (self.NEW_SCRIPT, '*Create a script'))
        choices.insert(0, (self.UPLOAD_BIN, '*Upload a new file'))

        return choices

    def handle(self, request, context):
        try:
            extra = {}
            bin_url = "%s://%s" % (context["job_binary_type"],
                                   context["job_binary_url"])
            if(context["job_binary_type"] == "internal-db"):
                bin_url = self.handle_internal(request, context)
            elif(context["job_binary_type"] == "swift"):
                extra = self.handle_swift(request, context)

            bin_object = saharaclient.job_binary_create(
                request,
                context["job_binary_name"],
                bin_url,
                context["job_binary_description"],
                extra)
            messages.success(request, "Successfully created job binary")
            return bin_object
        except Exception:
            exceptions.handle(request,
                              _("Unable to create job binary"))
            return False

    def get_help_text(self, extra_context=None):
        text = ""
        extra_context = extra_context or {}
        if self.help_text_template:
            tmpl = template.loader.get_template(self.help_text_template)
            context = template.RequestContext(self.request, extra_context)
            text += tmpl.render(context)
        else:
            text += defaultfilters.linebreaks(force_text(self.help_text))
        return defaultfilters.safe(text)

    class Meta(object):
        name = _("Create Job Binary")
        help_text_template = ("project/data_processing.job_binaries/"
                              "_create_job_binary_help.html")

    def handle_internal(self, request, context):
        result = ""

        bin_id = context["job_binary_internal"]
        if(bin_id == self.UPLOAD_BIN):
            try:
                result = saharaclient.job_binary_internal_create(
                    request,
                    self.get_unique_binary_name(
                        request, request.FILES["job_binary_file"].name),
                    request.FILES["job_binary_file"].read())
                bin_id = result.id
            except Exception:
                exceptions.handle(request,
                                  _("Unable to upload job binary"))
                return None
        elif(bin_id == self.NEW_SCRIPT):
            try:
                result = saharaclient.job_binary_internal_create(
                    request,
                    self.get_unique_binary_name(
                        request, context["job_binary_script_name"]),
                    context["job_binary_script"])
                bin_id = result.id
            except Exception:
                exceptions.handle(request,
                                  _("Unable to create job binary"))
                return None

        return "internal-db://%s" % bin_id

    def handle_swift(self, request, context):
        username = context["job_binary_username"]
        password = context["job_binary_password"]

        extra = {
            "user": username,
            "password": password
        }
        return extra

    def get_unique_binary_name(self, request, base_name):
        try:
            internals = saharaclient.job_binary_internal_list(request)
        except Exception:
            internals = []
            exceptions.handle(request,
                              _("Failed to fetch internal binary list"))
        names = [internal.name for internal in internals]
        if base_name in names:
            return "%s_%s" % (base_name, uuid.uuid1())
        return base_name
