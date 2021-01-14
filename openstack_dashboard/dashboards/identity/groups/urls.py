# Copyright 2013 Hewlett-Packard Development Company, L.P.
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

from horizon.browsers.views import AngularIndexView

from openstack_dashboard.dashboards.identity.groups import panel
from openstack_dashboard.dashboards.identity.groups import views
from openstack_dashboard.utils import settings as setting_utils


if setting_utils.get_dict_config('ANGULAR_FEATURES', 'groups_panel'):
    title = panel.Groups.name
    urlpatterns = [
        url(r'^$', AngularIndexView.as_view(title=title), name='index'),
    ]
else:
    urlpatterns = [
        url(r'^$', views.IndexView.as_view(), name='index'),
        url(r'^create$', views.CreateView.as_view(), name='create'),
        url(r'^(?P<group_id>[^/]+)/update/$',
            views.UpdateView.as_view(), name='update'),
        url(r'^(?P<group_id>[^/]+)/manage_members/$',
            views.ManageMembersView.as_view(), name='manage_members'),
        url(r'^(?P<group_id>[^/]+)/add_members/$',
            views.NonMembersView.as_view(), name='add_members'),
    ]
