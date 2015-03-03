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
from django.conf.urls import patterns
from django.conf.urls.static import static  # noqa
from django.conf.urls import url
from django.contrib.staticfiles.urls import staticfiles_urlpatterns  # noqa

from openstack_auth import views as openstack_auth_views

import horizon

from openstack_dashboard.fiware_auth import urls as fiware_auth_urls
from openstack_dashboard.fiware_auth import forms as fiware_auth_forms
from openstack_dashboard.fiware_oauth2 import urls as fiware_oauth2_urls

urlpatterns = patterns(
    '',
    url(r'^$', 'openstack_dashboard.views.splash', name='splash'),
     # NOTE(garcianavalon) override to use our form
    url(r'^auth/login/$', openstack_auth_views.login, 
        {'form_class': fiware_auth_forms.LoginWithEmailForm}, name='login'),
    url(r'^auth/', include('openstack_auth.urls')),
    url(r'', include(horizon.urls)),
    url(r'', include(fiware_auth_urls)),
    url(r'', include(fiware_oauth2_urls)),
    url(r'^summernote/', include('django_summernote.urls')),
)


# Development static app and project media serving using the staticfiles app.
urlpatterns += staticfiles_urlpatterns()

# Convenience function for serving user-uploaded media during
# development. Only active if DEBUG==True and the URL prefix is a local
# path. Production media should NOT be served by Django.
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

if settings.DEBUG:
    urlpatterns += patterns(
        '',
        url(r'^500/$', 'django.views.defaults.server_error')
    )
