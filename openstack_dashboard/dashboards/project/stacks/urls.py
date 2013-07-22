# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

from django.conf.urls.defaults import patterns
from django.conf.urls.defaults import url

from openstack_dashboard.dashboards.project.stacks.views import CreateStackView
from openstack_dashboard.dashboards.project.stacks.views import DetailView
from openstack_dashboard.dashboards.project.stacks.views import IndexView
from openstack_dashboard.dashboards.project.stacks.views import JSONView
from openstack_dashboard.dashboards.project.stacks.views import ResourceView
from openstack_dashboard.dashboards.project.stacks.views \
    import SelectTemplateView

urlpatterns = patterns(
    '',
    url(r'^$', IndexView.as_view(), name='index'),
    url(r'^select_template$',
        SelectTemplateView.as_view(),
        name='select_template'),
    url(r'^launch$', CreateStackView.as_view(), name='launch'),
    url(r'^stack/(?P<stack_id>[^/]+)/$', DetailView.as_view(), name='detail'),
    url(r'^stack/(?P<stack_id>[^/]+)/(?P<resource_name>[^/]+)/$',
        ResourceView.as_view(), name='resource'),
    url(r'^get_d3_data/(?P<stack_id>[^/]+)/$',
        JSONView.as_view(), name='d3_data'),
)
