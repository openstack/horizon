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

from django.conf.urls import include
from django.conf.urls import url

from openstack_dashboard.dashboards.project.access_and_security.\
    api_access import urls as api_access_urls
from openstack_dashboard.dashboards.project.access_and_security.\
    floating_ips import urls as fip_urls
from openstack_dashboard.dashboards.project.access_and_security.\
    keypairs import urls as keypair_urls
from openstack_dashboard.dashboards.project.access_and_security.\
    security_groups import urls as sec_group_urls
from openstack_dashboard.dashboards.project.access_and_security import views


urlpatterns = [
    url(r'^$', views.IndexView.as_view(), name='index'),
    url(r'api_access/', include(api_access_urls, namespace='api_access')),
    url(r'keypairs/', include(keypair_urls, namespace='keypairs')),
    url(r'floating_ips/', include(fip_urls, namespace='floating_ips')),
    url(r'security_groups/',
        include(sec_group_urls, namespace='security_groups')),
]
