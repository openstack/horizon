# Copyright 2012 United States Government as represented by the
# Administrator of the National Aeronautics and Space Administration.
# All Rights Reserved.
#
# Copyright 2012 Nebula, Inc.
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

from django.conf.urls import url

from openstack_dashboard.dashboards.project.access_and_security.keypairs \
    import views


urlpatterns = [
    url(r'^create/$', views.CreateView.as_view(), name='create'),
    url(r'^import/$', views.ImportView.as_view(), name='import'),
    url(r'^(?P<keypair_name>[^/]+)/download/$', views.DownloadView.as_view(),
        name='download'),
    url(r'^(?P<keypair_name>[^/]+)/generate/$', views.GenerateView.as_view(),
        name='generate'),
    url(r'^(?P<keypair_name>[^/]+)/(?P<optional>[^/]+)/generate/$',
        views.GenerateView.as_view(), name='generate'),
    url(r'^(?P<keypair_name>[^/]+)/$', views.DetailView.as_view(),
        name='detail'),
]
