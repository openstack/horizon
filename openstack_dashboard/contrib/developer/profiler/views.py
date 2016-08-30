# Copyright 2016 Mirantis Inc.
# All Rights Reserved.
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

from django.utils.translation import ugettext_lazy as _
from django.views import generic

from horizon import views
from openstack_dashboard.api.rest import urls
from openstack_dashboard.api.rest import utils
from openstack_dashboard.contrib.developer.profiler import api


class IndexView(views.HorizonTemplateView):
    template_name = 'developer/profiler/index.html'
    page_title = _("OpenStack Profiler")

    def get_context_data(self, **kwargs):
        context = super(IndexView, self).get_context_data(**kwargs)
        return context


@urls.register
class Traces(generic.View):
    url_regex = r'profiler/traces$'

    @utils.ajax()
    def get(self, request):
        return api.list_traces(request)


@urls.register
class Trace(generic.View):
    url_regex = r'profiler/traces/(?P<trace_id>[^/]+)/$'

    @utils.ajax()
    def get(self, request, trace_id):
        return api.get_trace(request, trace_id)
