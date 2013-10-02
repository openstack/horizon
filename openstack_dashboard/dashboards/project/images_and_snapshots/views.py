# vim: tabstop=4 shiftwidth=4 softtabstop=4

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
from django.utils.translation import ugettext_lazy as _  # noqa

from horizon import exceptions
from horizon import tables
from horizon import tabs

from openstack_dashboard import api
from openstack_dashboard.api import base

from openstack_dashboard.dashboards.project.images_and_snapshots.images \
    import tables as images_tables
from openstack_dashboard.dashboards.project.images_and_snapshots.\
    volume_snapshots import tables as vol_snsh_tables
from openstack_dashboard.dashboards.project.images_and_snapshots.\
    volume_snapshots import tabs as vol_snsh_tabs


class IndexView(tables.MultiTableView):
    table_classes = (images_tables.ImagesTable,
                     vol_snsh_tables.VolumeSnapshotsTable)
    template_name = 'project/images_and_snapshots/index.html'

    def has_more_data(self, table):
        return getattr(self, "_more_%s" % table.name, False)

    def get_images_data(self):
        marker = self.request.GET.get(
            images_tables.ImagesTable._meta.pagination_param, None)
        try:
            # FIXME(gabriel): The paging is going to be strange here due to
            # our filtering after the fact.
            (all_images,
             self._more_images) = api.glance.image_list_detailed(self.request,
                                                                 marker=marker)
            images = [im for im in all_images
                      if im.container_format not in ['aki', 'ari']]
        except Exception:
            images = []
            exceptions.handle(self.request, _("Unable to retrieve images."))
        return images

    def get_volume_snapshots_data(self):
        if base.is_service_enabled(self.request, 'volume'):
            try:
                snapshots = api.cinder.volume_snapshot_list(self.request)
                volumes = api.cinder.volume_list(self.request)
                volumes = dict((v.id, v) for v in volumes)
            except Exception:
                snapshots = []
                volumes = {}
                exceptions.handle(self.request, _("Unable to retrieve "
                                                  "volume snapshots."))

            for snapshot in snapshots:
                volume = volumes.get(snapshot.volume_id)
                setattr(snapshot, '_volume', volume)

        else:
            snapshots = []
        return snapshots


class DetailView(tabs.TabView):
    tab_group_class = vol_snsh_tabs.SnapshotDetailTabs
    template_name = 'project/images_and_snapshots/snapshots/detail.html'
