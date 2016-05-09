# Copyright 2015, Alcatel-Lucent USA Inc.
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

from openstack_dashboard.dashboards.project.networks.ports.extensions.\
    allowed_address_pairs import views as project_views
from openstack_dashboard.dashboards.admin.networks.ports.extensions.\
    allowed_address_pairs import forms as admin_forms


class AddAllowedAddressPair(project_views.AddAllowedAddressPair):
    form_class = admin_forms.AddAllowedAddressPairForm
    submit_url = "horizon:admin:networks:ports:addallowedaddresspairs"
    success_url = 'horizon:admin:networks:ports:detail'
