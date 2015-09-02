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
from django.conf.urls import patterns
from django.conf.urls import url
from django.contrib.staticfiles.urls import staticfiles_urlpatterns  # noqa
from django.views.generic import TemplateView  # noqa

import horizon
from horizon.test.jasmine import jasmine


urlpatterns = patterns(
    '',
    url(r'', include(horizon.urls)),
    url(r"auth/login/", "django.contrib.auth.views.login",
        {'template_name': "auth/login.html"},
        name='login'),
    url(r'auth/', include('django.contrib.auth.urls')),
    url(r'^jasmine/.*?$', jasmine.dispatcher),
    url(r'^jasmine-legacy/$',
        TemplateView.as_view(
            template_name="horizon/jasmine/jasmine_legacy.html"),
        name='jasmine_tests'),
)

urlpatterns += staticfiles_urlpatterns()
