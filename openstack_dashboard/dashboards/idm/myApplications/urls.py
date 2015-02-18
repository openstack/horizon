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

from openstack_dashboard.dashboards.idm.myApplications import views


urlpatterns = patterns('',
    url(r'^$', views.IndexView.as_view(), name='index'),
    url(r'^create/$', views.CreateView.as_view(), name='create'),
   
    url(r'^(?P<application_id>[^/]+)/edit/info/$', 
        views.CreateApplicationFormHandleView.as_view(), name='info'),
    url(r'^(?P<application_id>[^/]+)/edit/avatar/$', 
        views.AvatarFormHandleView.as_view(), name='avatar'),
    url(r'^(?P<application_id>[^/]+)/edit/cancel/$', 
        views.CancelFormHandleView.as_view(), name='cancel'),
    url(r'^(?P<application_id>[^/]+)/edit/roles/create/$', 
        views.CreateRoleView.as_view(), name='roles_create'),
    url(r'^(?P<application_id>[^/]+)/edit/roles/(?P<role_id>[^/]+)/delete/$', 
        views.DeleteRoleView.as_view(), name='roles_delete'),
    url(r'^(?P<application_id>[^/]+)/edit/roles/(?P<role_id>[^/]+)/edit/$', 
        views.EditRoleView.as_view(), name='roles_edit'),
    url(r'^(?P<application_id>[^/]+)/edit/permissions/create/$', 
        views.CreatePermissionView.as_view(), name='permissions_create'),
    url(r'^(?P<application_id>[^/]+)/edit/$', 
        views.BaseApplicationsMultiFormView.as_view(), name='edit'), 
    url(r'^(?P<application_id>[^/]+)/step/avatar/$', 
        views.AvatarStepView.as_view(), name='avatar_step'),
    url(r'^(?P<application_id>[^/]+)/step/roles/$', 
        views.RolesView.as_view(), name='roles_index'),
    url(r'^(?P<application_id>[^/]+)/$', 
        views.DetailApplicationView.as_view(), name='detail'),
    url(r'^(?P<application_id>[^/]+)/edit/members/$', 
        views.AuthorizedMembersView.as_view(), name='members'),
    url(r'^(?P<application_id>[^/]+)/edit/organizations/$', 
        views.AuthorizedOrganizationsView.as_view(), name='organizations'),
)
