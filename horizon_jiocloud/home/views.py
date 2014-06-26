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

from django.template import RequestContext  # noqa
from django.views.generic import TemplateView
from django.http import HttpResponseRedirect
from django.core.urlresolvers import reverse_lazy
from horizon_jiocloud.api import keystoneapi
import logging as log


def HomeView(request):
	return HttpResponseRedirect(reverse_lazy('horizon:project:overview:index'))

class PageUnderConstructionView(TemplateView):
    template_name = "common/page-under-construction.html"

class ApiDocumentation(TemplateView):
    template_name = "common/api_documentation.html"

class ComputeView(TemplateView):
    template_name = "static/compute.html"

class ObjectStoreView(TemplateView):
    template_name = "static/object-store.html"

class BlockStoreView(TemplateView):
    template_name = "static/block-store.html"

class StarterGuideView(TemplateView):
    template_name = "common/starter-guide.html"

class FaqsView(TemplateView):
    template_name = "static/faqs.html"

class FeaturesView(TemplateView):
    template_name = "static/features.html"

class DocumentationView(TemplateView):
    template_name = "static/documentation.html"

