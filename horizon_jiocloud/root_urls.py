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
from django.conf.urls import include  # noqa
import openstack_dashboard.urls, horizon_jiocloud.urls

urlpatterns = None
print "=========vivek 1===================="
try:
    urlpatterns = patterns('',
        url(r'', include(openstack_dashboard.urls)),
        url(r'', include(horizon_jiocloud.urls, namespace='horizon_jiocloud')),
    )
except Exception as e:
    print e
print urlpatterns, "urlpatterns vivek"
print "=========vivek 2 urls===================="

#        url(r'', include(horizon_jiocloud.urls, namespace='horizon_jiocloud')),
