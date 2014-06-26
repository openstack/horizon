# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright 2013 Reliance Jio Infocomm, Ltd.
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

from django.conf.urls import patterns  # noqa
from django.conf.urls import url  # noqa
import views
from django.contrib.auth.decorators import login_required

urlpatterns = patterns('',
    url(r'^users/signup/$',
        views.UserSignupView.as_view(),
        name='signup'),
    url(r'^users/(?P<user_id>[a-z0-9]+)/activate/$',
        views.UserSMSActivateView.as_view(),
        name='user_sms_activation'),
    url(r'^users/activation_success/$',
        views.TemplateView.as_view(
            template_name="signup/sms_activation_success.html"
        ),
        name='user_sms_activation_success'),
    url(r'^regions/(?P<country_id>[a-z0-9]+)/$',
        views.regions,
        name='regions'),
    url(r'^cities/(?P<region_id>[a-z0-9]+)/$',
        views.cities,
        name='cities'),
)

