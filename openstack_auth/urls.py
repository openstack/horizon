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

from django.conf import settings
from django.urls import re_path
from django.views import generic

from openstack_auth import utils
from openstack_auth import views


urlpatterns = [
    re_path(r"^login/$", views.login, name='login'),
    re_path(r"^logout/$", views.logout, name='logout'),
    re_path(r'^switch/(?P<tenant_id>[^/]+)/$', views.switch,
            name='switch_tenants'),
    re_path(r'^switch_services_region/(?P<region_name>[^/]+)/$',
            views.switch_region,
            name='switch_services_region'),
    re_path(r'^switch_keystone_provider/(?P<keystone_provider>[^/]+)/$',
            views.switch_keystone_provider,
            name='switch_keystone_provider'),
    re_path(r'^switch_system_scope/$',
            views.switch_system_scope,
            name='switch_system_scope'),
]

if utils.allow_expired_passowrd_change():
    urlpatterns.append(
        re_path(r'^password/(?P<user_id>[^/]+)/$',
                views.PasswordView.as_view(),
                name='password')
    )

if settings.WEBSSO_ENABLED:
    urlpatterns += [
        re_path(r"^websso/$", views.websso, name='websso'),
        re_path(r"^error/$",
                generic.TemplateView.as_view(template_name="403.html"))
    ]
