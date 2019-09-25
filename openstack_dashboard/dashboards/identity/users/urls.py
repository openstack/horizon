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
from django.utils.translation import ugettext_lazy as _

from horizon.browsers.views import AngularIndexView
from openstack_dashboard.dashboards.identity.users import views
from openstack_dashboard.utils import settings as setting_utils


if setting_utils.get_dict_config('ANGULAR_FEATURES', 'users_panel'):
    title = _("Users")
    # new angular panel
    urlpatterns = [
        url(r'^$', AngularIndexView.as_view(title=title), name='index'),
    ]
else:
    urlpatterns = [
        url(r'^$', views.IndexView.as_view(), name='index'),
        url(r'^(?P<user_id>[^/]+)/update/$',
            views.UpdateView.as_view(), name='update'),
        url(r'^create/$', views.CreateView.as_view(), name='create'),
        url(r'^(?P<user_id>[^/]+)/detail/$',
            views.DetailView.as_view(), name='detail'),
        url(r'^(?P<user_id>[^/]+)/change_password/$',
            views.ChangePasswordView.as_view(), name='change_password'),
    ]
