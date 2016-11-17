# Copyright 2012 United States Government as represented by the
# Administrator of the National Aeronautics and Space Administration.
# All Rights Reserved.
#
# Copyright 2012 Nebula, Inc.
# Copyright 2012 OpenStack Foundation
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
Views for managing Images and Snapshots.
"""

from django.utils.translation import ugettext_lazy as _

from horizon import exceptions
from horizon import messages
from horizon import tables

from openstack_dashboard import api
from openstack_dashboard import policy

from openstack_dashboard.dashboards.project.images.images \
    import tables as images_tables


class IndexView(tables.DataTableView):
    table_class = images_tables.ImagesTable
    template_name = 'project/images/index.html'
    page_title = _("Images")

    def has_prev_data(self, table):
        return getattr(self, "_prev", False)

    def has_more_data(self, table):
        return getattr(self, "_more", False)

    def get_data(self):
        if not policy.check((("image", "get_images"),), self.request):
            msg = _("Insufficient privilege level to retrieve image list.")
            messages.info(self.request, msg)
            return []
        prev_marker = self.request.GET.get(
            images_tables.ImagesTable._meta.prev_pagination_param, None)

        if prev_marker is not None:
            marker = prev_marker
        else:
            marker = self.request.GET.get(
                images_tables.ImagesTable._meta.pagination_param, None)
        reversed_order = prev_marker is not None
        try:
            images, self._more, self._prev = api.glance.image_list_detailed(
                self.request,
                marker=marker,
                paginate=True,
                sort_dir='asc',
                sort_key='name',
                reversed_order=reversed_order)
        except Exception:
            images = []
            self._prev = self._more = False
            exceptions.handle(self.request, _("Unable to retrieve images."))
        return images
