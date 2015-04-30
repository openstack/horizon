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

import openstack_dashboard.dashboards.project. \
    data_processing.nodegroup_templates.views as views


urlpatterns = patterns('sahara.nodegroup_templates.views',
                       url(r'^$', views.NodegroupTemplatesView.as_view(),
                           name='index'),
                       url(r'^nodegroup-templates$',
                           views.NodegroupTemplatesView.as_view(),
                           name='nodegroup-templates'),
                       url(r'^create-nodegroup-template$',
                           views.CreateNodegroupTemplateView.as_view(),
                           name='create-nodegroup-template'),
                       url(r'^configure-nodegroup-template$',
                           views.ConfigureNodegroupTemplateView.as_view(),
                           name='configure-nodegroup-template'),
                       url(r'^(?P<template_id>[^/]+)$',
                           views.NodegroupTemplateDetailsView.as_view(),
                           name='details'),
                       url(r'^(?P<template_id>[^/]+)/copy$',
                           views.CopyNodegroupTemplateView.as_view(),
                           name='copy')
                       )
