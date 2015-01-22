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

from collections import defaultdict

from django.conf import settings
from django.core.urlresolvers import reverse
from django.template import defaultfilters as filters
from django.utils.http import urlencode
from django.utils.translation import ugettext_lazy as _
from django.utils.translation import ungettext_lazy

from horizon import tables
from horizon.utils.memoized import memoized  # noqa

from openstack_dashboard import api
from openstack_dashboard.api import base

NOT_LAUNCHABLE_FORMATS = ['aki', 'ari']


class LaunchImage(tables.LinkAction):
    name = "launch_image"
    verbose_name = _("Launch")
    url = "horizon:project:instances:launch"
    classes = ("ajax-modal", "btn-launch")
    icon = "cloud-upload"
    policy_rules = (("compute", "compute:create"),)

    def get_link_url(self, datum):
        base_url = reverse(self.url)

        if get_image_type(datum) == "image":
            source_type = "image_id"
        else:
            source_type = "instance_snapshot_id"

        params = urlencode({"source_type": source_type,
                            "source_id": self.table.get_object_id(datum)})
        return "?".join([base_url, params])

    def allowed(self, request, image=None):
        if image and image.container_format not in NOT_LAUNCHABLE_FORMATS:
            return image.status in ("active",)
        return False


class DeleteImage(tables.DeleteAction):
    @staticmethod
    def action_present(count):
        return ungettext_lazy(
            u"Delete Image",
            u"Delete Images",
            count
        )

    @staticmethod
    def action_past(count):
        return ungettext_lazy(
            u"Deleted Image",
            u"Deleted Images",
            count
        )

    policy_rules = (("image", "delete_image"),)

    def allowed(self, request, image=None):
        # Protected images can not be deleted.
        if image and image.protected:
            return False
        if image:
            return image.owner == request.user.tenant_id
        # Return True to allow table-level bulk delete action to appear.
        return True

    def delete(self, request, obj_id):
        api.glance.image_delete(request, obj_id)


class CreateImage(tables.LinkAction):
    name = "create"
    verbose_name = _("Create Image")
    url = "horizon:project:images:images:create"
    classes = ("ajax-modal",)
    icon = "plus"
    policy_rules = (("image", "add_image"),)


class EditImage(tables.LinkAction):
    name = "edit"
    verbose_name = _("Edit")
    url = "horizon:project:images:images:update"
    classes = ("ajax-modal",)
    icon = "pencil"
    policy_rules = (("image", "modify_image"),)

    def allowed(self, request, image=None):
        if image:
            return image.status in ("active",) and \
                image.owner == request.user.tenant_id
        # We don't have bulk editing, so if there isn't an image that's
        # authorized, don't allow the action.
        return False


class CreateVolumeFromImage(tables.LinkAction):
    name = "create_volume_from_image"
    verbose_name = _("Create Volume")
    url = "horizon:project:volumes:volumes:create"
    classes = ("ajax-modal",)
    icon = "camera"
    policy_rules = (("volume", "volume:create"),)

    def get_link_url(self, datum):
        base_url = reverse(self.url)
        params = urlencode({"image_id": self.table.get_object_id(datum)})
        return "?".join([base_url, params])

    def allowed(self, request, image=None):
        if (image and image.container_format not in NOT_LAUNCHABLE_FORMATS
                and base.is_service_enabled(request, 'volume')):
            return image.status == "active"
        return False


def filter_tenants():
    return getattr(settings, 'IMAGES_LIST_FILTER_TENANTS', [])


@memoized
def filter_tenant_ids():
    return map(lambda ft: ft['tenant'], filter_tenants())


class OwnerFilter(tables.FixedFilterAction):
    def get_fixed_buttons(self):
        def make_dict(text, tenant, icon):
            return dict(text=text, value=tenant, icon=icon)

        buttons = [make_dict(_('Project'), 'project', 'fa-home')]
        for button_dict in filter_tenants():
            new_dict = button_dict.copy()
            new_dict['value'] = new_dict['tenant']
            buttons.append(new_dict)
        buttons.append(make_dict(_('Shared with Me'), 'shared',
                                 'fa-share-square-o'))
        buttons.append(make_dict(_('Public'), 'public', 'fa-group'))
        return buttons

    def categorize(self, table, images):
        user_tenant_id = table.request.user.tenant_id
        tenants = defaultdict(list)
        for im in images:
            categories = get_image_categories(im, user_tenant_id)
            for category in categories:
                tenants[category].append(im)
        return tenants


def get_image_categories(im, user_tenant_id):
    categories = []
    if im.is_public:
        categories.append('public')
    if im.owner == user_tenant_id:
        categories.append('project')
    elif im.owner in filter_tenant_ids():
        categories.append(im.owner)
    elif not im.is_public:
        categories.append('shared')
    return categories


def get_image_name(image):
    return getattr(image, "name", None) or image.id


def get_image_type(image):
    return getattr(image, "properties", {}).get("image_type", "image")


def get_format(image):
    format = getattr(image, "disk_format", "")
    # The "container_format" attribute can actually be set to None,
    # which will raise an error if you call upper() on it.
    if format is not None:
        return format.upper()


class UpdateRow(tables.Row):
    ajax = True

    def get_data(self, request, image_id):
        image = api.glance.image_get(request, image_id)
        return image

    def load_cells(self, image=None):
        super(UpdateRow, self).load_cells(image)
        # Tag the row with the image category for client-side filtering.
        image = self.datum
        my_tenant_id = self.table.request.user.tenant_id
        image_categories = get_image_categories(image, my_tenant_id)
        for category in image_categories:
            self.classes.append('category-' + category)


class ImagesTable(tables.DataTable):
    STATUS_CHOICES = (
        ("active", True),
        ("saving", None),
        ("queued", None),
        ("pending_delete", None),
        ("killed", False),
        ("deleted", False),
    )
    name = tables.Column(get_image_name,
                         link=("horizon:project:images:images:detail"),
                         verbose_name=_("Image Name"))
    image_type = tables.Column(get_image_type,
                               verbose_name=_("Type"),
                               filters=(filters.title,))
    status = tables.Column("status",
                           filters=(filters.title,),
                           verbose_name=_("Status"),
                           status=True,
                           status_choices=STATUS_CHOICES)
    public = tables.Column("is_public",
                           verbose_name=_("Public"),
                           empty_value=False,
                           filters=(filters.yesno, filters.capfirst))
    protected = tables.Column("protected",
                              verbose_name=_("Protected"),
                              empty_value=False,
                              filters=(filters.yesno, filters.capfirst))
    disk_format = tables.Column(get_format, verbose_name=_("Format"))
    size = tables.Column("size",
                         filters=(filters.filesizeformat,),
                         attrs=({"data-type": "size"}),
                         verbose_name=_("Size"))

    class Meta:
        name = "images"
        row_class = UpdateRow
        status_columns = ["status"]
        verbose_name = _("Images")
        table_actions = (OwnerFilter, CreateImage, DeleteImage,)
        row_actions = (LaunchImage, CreateVolumeFromImage,
                       EditImage, DeleteImage,)
        pagination_param = "image_marker"
