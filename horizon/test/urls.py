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

"""
URL patterns for testing Horizon views.
"""

from django.conf.urls import include
from django.contrib.auth import views
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from django.urls import re_path
from django.views.generic import TemplateView

import horizon
import horizon.base
from horizon.test.jasmine import jasmine


urlpatterns = [
    re_path(r'', horizon.base._wrapped_include(horizon.urls)),
    re_path(r"auth/login/",
            views.LoginView.as_view(template_name="auth/login.html"),
            name='login'),
    re_path(r'auth/', include('django.contrib.auth.urls')),
    re_path(r'^jasmine/.*?$', jasmine.dispatcher),
    re_path(r'^jasmine-legacy/$',
            TemplateView.as_view(
                template_name="horizon/jasmine/jasmine_legacy.html"),
            name='jasmine_tests'),
]

urlpatterns += staticfiles_urlpatterns()
