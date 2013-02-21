# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright 2012,  Nachi Ueno,  NTT MCL,  Inc.
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

import logging

from horizon import tabs
from .tabs import PortDetailTabs
from .forms import (AddInterface, SetGatewayForm)
from openstack_dashboard.dashboards.project.routers.ports import views


LOG = logging.getLogger(__name__)


class AddInterfaceView(views.AddInterfaceView):
    form_class = AddInterface
    template_name = 'admin/routers/ports/create.html'
    success_url = 'horizon:admin:routers:detail'
    failure_url = 'horizon:admin:routers:detail'


class SetGatewayView(views.SetGatewayView):
    form_class = SetGatewayForm
    template_name = 'admin/routers/ports/setgateway.html'
    success_url = 'horizon:admin:routers:index'
    failure_url = 'horizon:admin:routers:index'


class DetailView(tabs.TabView):
    tab_group_class = PortDetailTabs
    template_name = 'admin/networks/ports/detail.html'
