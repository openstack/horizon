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

from django.conf import settings
from django.conf.urls import include
from django.conf.urls import url
from django.views.generic import TemplateView  # noqa
from django.views import i18n

from horizon.test.jasmine import jasmine
from horizon import views

urlpatterns = [
    url(r'^home/$', views.user_home, name='user_home')
]

# Client-side i18n URLconf.
urlpatterns.extend([
    url(r'^i18n/js/(?P<packages>\S+?)/$',
        i18n.javascript_catalog,
        name='jsi18n'),
    url(r'^i18n/setlang/$',
        i18n.set_language,
        name="set_language"),
    url(r'^i18n/', include('django.conf.urls.i18n'))
])

if settings.DEBUG:
    urlpatterns.extend([
        url(r'^jasmine-legacy/$',
            TemplateView.as_view(
                template_name="horizon/jasmine/jasmine_legacy.html"),
            name='jasmine_tests'),
        url(r'^jasmine/.*?$', jasmine.dispatcher),
    ])
