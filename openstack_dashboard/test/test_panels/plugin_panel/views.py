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

from horizon import views


class IndexView(views.HorizonTemplateView):
    template_name = 'admin/plugin_panel/index.html'
    page_title = 'Plugin-based Panel'


class TestBannerView(views.HorizonTemplateView):
    template_name = 'admin/plugin_panel/header.html'

    def get_context_data(self, **kwargs):
        context = super(TestBannerView, self).get_context_data(**kwargs)

        context['message'] = "sample context"
        return context
