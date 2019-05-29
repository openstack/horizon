# Copyright 2018 SUSE Linux GmbH
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

from openstack_dashboard.dashboards.identity.application_credentials \
    import views


urlpatterns = [
    url(r'^$', views.IndexView.as_view(), name='index'),
    url(r'^create/$', views.CreateView.as_view(), name='create'),
    url(r'^(?P<application_credential_id>[^/]+)/detail/$',
        views.DetailView.as_view(), name='detail'),
    url(r'^success/$',
        views.CreateSuccessfulView.as_view(), name='success'),
    url(r'^download_openrc/$',
        views.download_rc_file, name='download_openrc'),
    url(r'^download_kubeconfig/$',
        views.download_kubeconfig_file, name='download_kubeconfig'),
    url(r'^download_clouds_yaml/$',
        views.download_clouds_yaml_file, name='download_clouds_yaml'),
]
