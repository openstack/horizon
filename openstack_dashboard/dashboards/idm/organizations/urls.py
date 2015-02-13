# Copyright (C) 2014 Universidad Politecnica de Madrid
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

from django.conf.urls import patterns
from django.conf.urls import url

from openstack_dashboard.dashboards.idm.organizations import views

urlpatterns = patterns('',
    url(r'^$', views.IndexView.as_view(), name='index'),
    url(r'^create/$', views.CreateOrganizationView.as_view(), name='create'),
    url(r'^(?P<organization_id>[^/]+)/$', 
            views.DetailOrganizationView.as_view(), name='detail'), 
    url(r'^(?P<organization_id>[^/]+)/edit/$', 
            views.BaseOrganizationsMultiFormView.as_view(), name='edit'), 
    url(r'^(?P<organization_id>[^/]+)/edit/info/$', 
            views.InfoFormHandleView.as_view(), name='info'),
    url(r'^(?P<organization_id>[^/]+)/edit/contact/$', 
            views.ContactFormHandleView.as_view(), name='contact'),
    url(r'^(?P<organization_id>[^/]+)/edit/avatar/$', 
            views.AvatarFormHandleView.as_view(), name='avatar'),
    url(r'^(?P<organization_id>[^/]+)/edit/cancel/$', 
            views.CancelFormHandleView.as_view(), name='cancel'),
    url(r'^(?P<organization_id>[^/]+)/edit/members/$', 
        views.OrganizationMembersView.as_view(), name='members'),
)
