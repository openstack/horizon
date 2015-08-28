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
import logging

from django.core.urlresolvers import reverse_lazy
from django import http
from django.utils.translation import ugettext_lazy as _
from django.views import generic

from horizon import exceptions
from horizon import forms
from horizon import views as horizon_views

from openstack_dashboard.contrib.sahara.content.data_processing.utils \
    import helpers
import openstack_dashboard.contrib.sahara.content.data_processing.wizard \
    .forms as wizforms


LOG = logging.getLogger(__name__)


class WizardView(horizon_views.APIView):
    template_name = 'project/data_processing.wizard/wizard.html'
    page_title = _("Data Processing Guides")

    def get_data(self, request, context, *args, **kwargs):
        try:
            context["test"] = "test data"
        except Exception:
            msg = _('Unable to show guides')
            exceptions.handle(self.request, msg)
        return context


class ClusterGuideView(horizon_views.APIView):
    template_name = 'project/data_processing.wizard/cluster_guide.html'
    page_title = _("Guided Cluster Creation")


class ResetClusterGuideView(generic.RedirectView):
    pattern_name = 'horizon:project:data_processing.wizard:cluster_guide'

    def get(self, request, *args, **kwargs):
        if kwargs["reset_cluster_guide"]:
            hlps = helpers.Helpers(request)
            hlps.reset_guide()
        return http.HttpResponseRedirect(reverse_lazy(self.pattern_name))


class JobExecutionGuideView(horizon_views.APIView):
    template_name = 'project/data_processing.wizard/jobex_guide.html'
    page_title = _("Guided Job Execution")

    def show_data_sources(self):
        try:
            if self.request.session["guide_job_type"] in ["Spark", "Storm",
                                                          "Java"]:
                return False
            return True
        except Exception:
            return True


class ResetJobExGuideView(generic.RedirectView):
    pattern_name = 'horizon:project:data_processing.wizard:jobex_guide'

    def get(self, request, *args, **kwargs):
        if kwargs["reset_jobex_guide"]:
            hlps = helpers.Helpers(request)
            hlps.reset_job_guide()
        return http.HttpResponseRedirect(reverse_lazy(self.pattern_name))


class PluginSelectView(forms.ModalFormView):
    form_class = wizforms.ChoosePluginForm
    success_url = reverse_lazy(
        'horizon:project:data_processing.wizard:cluster_guide')
    classes = ("ajax-modal")
    template_name = "project/data_processing.wizard/plugin_select.html"
    page_title = _("Choose plugin and version")


class JobTypeSelectView(forms.ModalFormView):
    form_class = wizforms.ChooseJobTypeForm
    success_url = reverse_lazy(
        'horizon:project:data_processing.wizard:jobex_guide')
    classes = ("ajax-modal")
    template_name = "project/data_processing.wizard/job_type_select.html"
    page_title = _("Choose job type")
