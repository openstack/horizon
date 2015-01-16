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

from django.conf.urls import patterns
from django.conf.urls import url

from openstack_dashboard.dashboards.project. \
    data_processing.wizard import views


urlpatterns = patterns('',
                       url(r'^$', views.WizardView.as_view(), name='index'),
                       url(r'^cluster_guide$',
                           views.ClusterGuideView.as_view(),
                           name='cluster_guide'),
                       url(r'^cluster_guide/(?P<reset_cluster_guide>[^/]+)/$',
                           views.ResetClusterGuideView.as_view(),
                           name='reset_cluster_guide'),
                       url(r'^jobex_guide$',
                           views.JobExecutionGuideView.as_view(),
                           name='jobex_guide'),
                       url(r'^jobex_guide/(?P<reset_jobex_guide>[^/]+)/$',
                           views.ResetJobExGuideView.as_view(),
                           name='reset_jobex_guide'),
                       url(r'^plugin_select$',
                           views.PluginSelectView.as_view(),
                           name='plugin_select'),
                       url(r'^job_type_select$',
                           views.JobTypeSelectView.as_view(),
                           name='job_type_select'),
                       )
