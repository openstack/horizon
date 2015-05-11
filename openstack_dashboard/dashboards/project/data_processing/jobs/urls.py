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


from django.conf.urls import patterns
from django.conf.urls import url

import openstack_dashboard.dashboards.project.data_processing. \
    jobs.views as views


urlpatterns = patterns('',
                       url(r'^$', views.JobsView.as_view(),
                           name='index'),
                       url(r'^$', views.JobsView.as_view(),
                           name='jobs'),
                       url(r'^create-job$',
                           views.CreateJobView.as_view(),
                           name='create-job'),
                       url(r'^launch-job$',
                           views.LaunchJobView.as_view(),
                           name='launch-job'),
                       url(r'^launch-job-new-cluster$',
                           views.LaunchJobNewClusterView.as_view(),
                           name='launch-job-new-cluster'),
                       url(r'^choose-plugin$',
                           views.ChoosePluginView.as_view(),
                           name='choose-plugin'),
                       url(r'^(?P<job_id>[^/]+)$',
                           views.JobDetailsView.as_view(),
                           name='details'))
