# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright 2012,  Nachi Ueno,  NTT MCL,  Inc.
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

from django.conf.urls.defaults import patterns, url

from .views import (IndexView, CreateView, DetailView)
from .ports.views import (AddInterfaceView, SetGatewayView)


urlpatterns = patterns('horizon.dashboards.project.routers.views',
    url(r'^$', IndexView.as_view(), name='index'),
    url(r'^create/$', CreateView.as_view(), name='create'),
    url(r'^(?P<router_id>[^/]+)/$',
        DetailView.as_view(),
        name='detail'),
    url(r'^(?P<router_id>[^/]+)/addinterface', AddInterfaceView.as_view(),
        name='addinterface'),
    url(r'^(?P<router_id>[^/]+)/setgateway',
        SetGatewayView.as_view(),
        name='setgateway'),
)
