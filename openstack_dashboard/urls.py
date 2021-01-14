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
URL patterns for the OpenStack Dashboard.
"""

from django.conf import settings
from django.conf.urls import include
from django.conf.urls.static import static
from django.conf.urls import url
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from django.views import defaults

import horizon
import horizon.base
from horizon.browsers import views as browsers_views
from horizon.decorators import require_auth

from openstack_dashboard.api import rest
from openstack_dashboard import views

urlpatterns = [
    url(r'^$', views.splash, name='splash'),
    url(r'^api/', include(rest.urls)),
    url(r'^header/', views.ExtensibleHeaderView.as_view()),
    url(r'', horizon.base._wrapped_include(horizon.urls)),
]

# add URL for ngdetails
ngdetails_url = url(r'^ngdetails/',
                    browsers_views.AngularDetailsView.as_view(),
                    name='ngdetails')
urlpatterns.append(ngdetails_url)
horizon.base._decorate_urlconf([ngdetails_url], require_auth)

for u in settings.AUTHENTICATION_URLS:
    urlpatterns.append(url(r'^auth/', include(u)))

# Development static app and project media serving using the staticfiles app.
urlpatterns += staticfiles_urlpatterns()

# Convenience function for serving user-uploaded media during
# development. Only active if DEBUG==True and the URL prefix is a local
# path. Production media should NOT be served by Django.
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

if settings.DEBUG:
    urlpatterns.append(url(r'^500/$', defaults.server_error))
