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

from django.utils.translation import ugettext_lazy as _

from horizon import browsers

from openstack_dashboard.dashboards.project.containers import tables


class ContainerBrowser(browsers.ResourceBrowser):
    name = "swift"
    verbose_name = _("Swift")
    navigation_table_class = tables.ContainersTable
    content_table_class = tables.ObjectsTable
    navigable_item_name = _("Container")
    navigation_kwarg_name = "container_name"
    content_kwarg_name = "subfolder_path"
    has_breadcrumb = True
    breadcrumb_url = "horizon:project:containers:index"
