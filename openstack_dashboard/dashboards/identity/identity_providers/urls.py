# Copyright (C) 2015 Yahoo! Inc. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

from django.conf.urls import include
from django.conf.urls import url

from openstack_dashboard.dashboards.identity.identity_providers.protocols \
    import urls as protocol_urls
from openstack_dashboard.dashboards.identity.identity_providers \
    import views

urlpatterns = [
    url(r'^$', views.IndexView.as_view(), name='index'),
    url(r'^(?P<identity_provider_id>[^/]+)/detail/$',
        views.DetailView.as_view(), name='detail'),
    url(r'^(?P<identity_provider_id>[^/]+)/detail/'
        '\?tab=idp_details__protocols$',
        views.DetailView.as_view(),
        name='protocols_tab'),
    url(r'^(?P<identity_provider_id>[^/]+)/update/$',
        views.UpdateView.as_view(), name='update'),
    url(r'^register/$', views.RegisterView.as_view(), name='register'),
    url(r'(?P<identity_provider_id>[^/]+)/protocols/',
        include(protocol_urls, namespace='protocols')),
]
