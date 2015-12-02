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

from horizon import tables

from openstack_dashboard import api
from openstack_dashboard.dashboards.project.images.images \
    import tables as project_tables


class AdminCreateImage(project_tables.CreateImage):
    url = "horizon:admin:images:create"


class AdminDeleteImage(project_tables.DeleteImage):
    def allowed(self, request, image=None):
        if image and image.protected:
            return False
        else:
            return True


class AdminEditImage(project_tables.EditImage):
    url = "horizon:admin:images:update"

    def allowed(self, request, image=None):
        return True


class UpdateMetadata(tables.LinkAction):
    name = "update_metadata"
    verbose_name = _("Update Metadata")
    ajax = False
    icon = "pencil"
    attrs = {"ng-controller": "MetadataModalHelperController as modal"}

    def __init__(self, attrs=None, **kwargs):
        kwargs['preempt'] = True
        super(UpdateMetadata, self).__init__(attrs, **kwargs)

    def get_link_url(self, datum):
        image_id = self.table.get_object_id(datum)
        self.attrs['ng-click'] = (
            "modal.openMetadataModal('image', '%s', true)" % image_id)
        return "javascript:void(0);"


class UpdateRow(tables.Row):
    ajax = True

    def get_data(self, request, image_id):
        image = api.glance.image_get(request, image_id)
        return image


class AdminImageFilterAction(tables.FilterAction):
    filter_type = "server"
    filter_choices = (('name', _("Image Name ="), True),
                      ('status', _('Status ='), True),
                      ('disk_format', _('Format ='), True),
                      ('size_min', _('Min. Size (MB) ='), True),
                      ('size_max', _('Max. Size (MB) ='), True))


class AdminImagesTable(project_tables.ImagesTable):
    name = tables.Column("name",
                         link="horizon:admin:images:detail",
                         verbose_name=_("Image Name"))
    tenant = tables.Column("tenant_name", verbose_name=_("Project"))

    class Meta(object):
        name = "images"
        row_class = UpdateRow
        status_columns = ["status"]
        verbose_name = _("Images")
        table_actions = (AdminCreateImage, AdminDeleteImage,
                         AdminImageFilterAction)
        row_actions = (AdminEditImage, UpdateMetadata, AdminDeleteImage)
        columns = ('tenant', 'name', 'image_type', 'status', 'public',
                   'protected', 'disk_format', 'size')
