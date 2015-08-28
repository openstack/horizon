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

import openstack_dashboard.contrib.sahara.content.data_processing. \
    clusters.views as views


urlpatterns = patterns('',
                       url(r'^$', views.ClustersView.as_view(),
                           name='index'),
                       url(r'^$', views.ClustersView.as_view(),
                           name='clusters'),
                       url(r'^create-cluster$',
                           views.CreateClusterView.as_view(),
                           name='create-cluster'),
                       url(r'^configure-cluster$',
                           views.ConfigureClusterView.as_view(),
                           name='configure-cluster'),
                       url(r'^(?P<cluster_id>[^/]+)$',
                           views.ClusterDetailsView.as_view(),
                           name='details'),
                       url(r'^(?P<cluster_id>[^/]+)/events$',
                           views.ClusterEventsView.as_view(),
                           name='events'),
                       url(r'^(?P<cluster_id>[^/]+)/scale$',
                           views.ScaleClusterView.as_view(),
                           name='scale'))
