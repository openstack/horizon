# Copyright (C) 2014 Universidad Politecnica de Madrid
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
# implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from django.conf.urls import patterns
from django.conf.urls import url

from openstack_dashboard.fiware_oauth2 import views


# NOTE(garcianavalon) following 
# https://github.com/ging/fi-ware-idm/wiki/Using-the-FI-LAB-instance

urlpatterns = patterns(
    'fiware_oauth2.views',
    url(r"^oauth2/authorize/$", views.AuthorizeView.as_view(), 
                            name='fiware_oauth2_authorize'),
    url(r"^oauth2/authorize/cancel/$", views.cancel_authorize, 
                            name='fiware_oauth2_cancel_authorize'),
    url(r"^oauth2/token$", views.AccessTokenView.as_view(), 
                            name='fiware_oauth2_access_token'),
    url(r"^user", views.UserInfoView.as_view(), 
                            name='fiware_oauth2_user_info'),
)