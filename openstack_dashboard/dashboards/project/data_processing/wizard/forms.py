# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
# implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from django import template
from django.template import defaultfilters
from django.utils.encoding import force_text
from django.utils.translation import ugettext_lazy as _

from horizon import exceptions
from horizon import forms
from horizon import messages

from openstack_dashboard.api import sahara as saharaclient
from openstack_dashboard.dashboards.project.data_processing.utils \
    import helpers


class ChoosePluginForm(forms.SelfHandlingForm):
    def __init__(self, request, *args, **kwargs):
        super(ChoosePluginForm, self).__init__(request, *args, **kwargs)
        self._generate_plugin_version_fields(request)
        self.help_text_template = ("project/data_processing.wizard/"
                                   "_plugin_select_help.html")

    def handle(self, request, context):
        try:
            hlps = helpers.Helpers(request)
            hlps.reset_guide()
            plugin_name = context["plugin_name"]
            request.session["plugin_name"] = plugin_name
            request.session["plugin_version"] = (
                context[plugin_name + "_version"])
            messages.success(request, _("Cluster type chosen"))
            return True
        except Exception:
            exceptions.handle(request,
                              _("Unable to set cluster type"))
            return False

    def _generate_plugin_version_fields(self, request):
        sahara = saharaclient.client(request)
        plugins = sahara.plugins.list()
        plugin_choices = [(plugin.name, plugin.title) for plugin in plugins]

        self.fields["plugin_name"] = forms.ChoiceField(
            label=_("Plugin Name"),
            choices=plugin_choices,
            widget=forms.Select(attrs={"class": "switchable",
                                       "data-slug": "plugin"}))

        for plugin in plugins:
            field_name = plugin.name + "_version"
            choice_field = forms.ChoiceField(
                label=_("Version"),
                required=False,
                choices=[(version, version) for version in plugin.versions],
                widget=forms.Select(
                    attrs={"class": "switched",
                           "data-switch-on": "plugin",
                           "data-plugin-" + plugin.name: plugin.title})
            )
            self.fields[field_name] = choice_field

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
        name = _("Choose plugin type and version")


class ChooseJobTypeForm(forms.SelfHandlingForm):
    guide_job_type = forms.ChoiceField(
        label=_("Job Type"),
        widget=forms.Select())

    def __init__(self, request, *args, **kwargs):
        super(ChooseJobTypeForm, self).__init__(request, *args, **kwargs)
        self.help_text_template = ("project/data_processing.wizard/"
                                   "_job_type_select_help.html")

        self.fields["guide_job_type"].choices = \
            self.populate_guide_job_type_choices()

    def populate_guide_job_type_choices(self):
        choices = [(x, helpers.JOB_TYPE_MAP[x][0])
                   for x in helpers.JOB_TYPE_MAP]
        return choices

    def handle(self, request, context):
        try:
            hlps = helpers.Helpers(request)
            job_type = context["guide_job_type"]
            if force_text(request.session.get("guide_job_type")) != (
                    force_text(helpers.JOB_TYPE_MAP[job_type][0])):
                hlps.reset_job_guide()
                request.session["guide_job_type"] = (
                    helpers.JOB_TYPE_MAP[job_type][0])
                messages.success(request, _("Job type chosen"))
            return True
        except Exception:
            exceptions.handle(request,
                              _("Unable to set job type"))
            return False
