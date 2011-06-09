# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright 2010 United States Government as represented by the
# Administrator of the National Aeronautics and Space Administration.
# All Rights Reserved.
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

from django.conf.urls.defaults import *
from django.conf import settings
from django.contrib import admin
from django.views import generic as generic_views
import django.views.i18n
from registration import forms as reg_forms


admin.autodiscover()

urlpatterns = patterns('',
    url(r'^$', 'dashboard.views.index', name='index'),
    url(r'^i18n/setlang', django.views.i18n.set_language),
    url(r'^accounts/register/$',
        'registration.views.register',
        {'form_class': reg_forms.RegistrationFormUniqueEmail},
        name='registration_register'),
    url(r'^accounts/', include('registration.urls')),
    url(r'^project/', include('django_openstack.nova.urls.project')),
    url(r'^region/', include('django_openstack.nova.urls.region')),
    url(r'^admin/project/', include('django_openstack.nova.urls.admin_project')),
    url(r'^admin/roles/', include('django_openstack.nova.urls.admin_roles')),
    url(r'^admin/', include(admin.site.urls)),
    url(r'^syspanel/', include('django_nova_syspanel.urls')),
)

urlpatterns += patterns('',
    # TODO(devcamcar): Move permission denied template into django-openstack.
    url(r'^denied/$',
        generic_views.TemplateView.as_view(template_name='permission_denied.html'),
        {'name': 'dashboard_permission_denied'}),
    url(r'^unavailable/$',
        generic_views.TemplateView.as_view(template_name='unavailable.html'),
        {'name': 'nova_unavailable'}),
)

urlpatterns += patterns('',
     (r'^%s(?P<path>.*)$' % settings.MEDIA_URL[1:],
      'django.views.static.serve',
      {'document_root': settings.MEDIA_ROOT,
       'show_indexes': True}),
 )
