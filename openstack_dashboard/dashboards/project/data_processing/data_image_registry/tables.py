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

import logging

from django import template
from django.utils.translation import ugettext_lazy as _
from django.utils.translation import ungettext_lazy

from horizon import tables

from openstack_dashboard.api import sahara as saharaclient


LOG = logging.getLogger(__name__)


class EditTagsAction(tables.LinkAction):
    name = "edit_tags"
    verbose_name = _("Edit Tags")
    url = "horizon:project:data_processing.data_image_registry:edit_tags"
    classes = ("ajax-modal",)


def tags_to_string(image):
    template_name = (
        'project/data_processing.data_image_registry/_list_tags.html')
    context = {"image": image}
    return template.loader.render_to_string(template_name, context)


class RegisterImage(tables.LinkAction):
    name = "register"
    verbose_name = _("Register Image")
    url = "horizon:project:data_processing.data_image_registry:register"
    classes = ("ajax-modal",)
    icon = "plus"


class UnregisterImages(tables.DeleteAction):
    @staticmethod
    def action_present(count):
        return ungettext_lazy(
            u"Unregister Image",
            u"Unregister Images",
            count
        )

    @staticmethod
    def action_past(count):
        return ungettext_lazy(
            u"Unregistered Image",
            u"Unregistered Images",
            count
        )

    def delete(self, request, obj_id):
        saharaclient.image_unregister(request, obj_id)


class ImageRegistryTable(tables.DataTable):
    name = tables.Column("name",
                         verbose_name=_("Image"),
                         link=("horizon:project:"
                               "images:images:detail"))
    tags = tables.Column(tags_to_string,
                         verbose_name=_("Tags"))

    class Meta(object):
        name = "image_registry"
        verbose_name = _("Image Registry")
        table_actions = (RegisterImage, UnregisterImages,)
        row_actions = (EditTagsAction, UnregisterImages,)
