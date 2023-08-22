# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
# implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from django.conf.urls import include
from django.urls import re_path
from django.views import generic

from openstack_auth import views


urlpatterns = [
    re_path(r"", include('openstack_auth.urls')),
    re_path(r"^websso/$", views.websso, name='websso'),
    re_path(r"^$",
            generic.TemplateView.as_view(template_name="auth/blank.html")),
    re_path(r'^totp/(?P<user_name>[^/]+)/$',
            views.TotpView.as_view(),
            name='totp')

]
