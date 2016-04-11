# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

from django.conf.urls import url

from openstack_dashboard.dashboards.project.stacks import views

urlpatterns = [
    url(r'^$', views.IndexView.as_view(), name='index'),
    url(r'^select_template$',
        views.SelectTemplateView.as_view(),
        name='select_template'),
    url(r'^launch$', views.CreateStackView.as_view(), name='launch'),
    url(r'^preview_template$',
        views.PreviewTemplateView.as_view(), name='preview_template'),
    url(r'^preview$', views.PreviewStackView.as_view(), name='preview'),
    url(r'^preview_details$',
        views.PreviewStackDetailsView.as_view(), name='preview_details'),
    url(r'^stack/(?P<stack_id>[^/]+)/$',
        views.DetailView.as_view(), name='detail'),
    url(r'^(?P<stack_id>[^/]+)/change_template$',
        views.ChangeTemplateView.as_view(), name='change_template'),
    url(r'^(?P<stack_id>[^/]+)/edit_stack$',
        views.EditStackView.as_view(), name='edit_stack'),
    url(r'^stack/(?P<stack_id>[^/]+)/(?P<resource_name>[^/]+)/$',
        views.ResourceView.as_view(), name='resource'),
    url(r'^get_d3_data/(?P<stack_id>[^/]+)/$',
        views.JSONView.as_view(), name='d3_data'),
]
