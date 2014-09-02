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

from django.core.urlresolvers import reverse
from django.utils import http
from django.utils.translation import ugettext_lazy as _

from horizon import tables

from openstack_dashboard import api


# Most of the following image custom properties can be found in the glance
# project at glance.api.v2.images.RequestDeserializer.

# Properties that cannot be edited
READONLY_PROPERTIES = ['checksum', 'container_format', 'created_at', 'deleted',
    'deleted_at', 'direct_url', 'disk_format', 'file', 'id', 'is_public',
    'location', 'owner', 'schema', 'self', 'size',
    'status', 'tags', 'updated_at', 'virtual_size']

# Properties that cannot be deleted
REQUIRED_PROPERTIES = ['checksum', 'container_format', 'created_at', 'deleted',
    'deleted_at', 'direct_url', 'disk_format', 'file', 'id', 'is_public',
    'location', 'min_disk', 'min_ram', 'name', 'owner', 'protected', 'schema',
    'self', 'size', 'status', 'tags', 'updated_at', 'virtual_size',
    'visibility']


class PropertyDelete(tables.DeleteAction):
    data_type_singular = _("Property")
    data_type_plural = _("Properties")

    def allowed(self, request, prop=None):
        if prop and prop.key in REQUIRED_PROPERTIES:
            return False
        return True

    def delete(self, request, obj_ids):
        api.glance.image_delete_properties(request, self.table.kwargs['id'],
                                           [obj_ids])


class PropertyCreate(tables.LinkAction):
    name = "create"
    verbose_name = _("Create Property")
    url = "horizon:admin:images:properties:create"
    classes = ("ajax-modal",)
    icon = "plus"

    def get_link_url(self, custom_property=None):
        return reverse(self.url, args=[self.table.kwargs['id']])


class PropertyEdit(tables.LinkAction):
    name = "edit"
    verbose_name = _("Edit")
    url = "horizon:admin:images:properties:edit"
    classes = ("btn-edit", "ajax-modal")

    def allowed(self, request, prop=None):
        if prop and prop.key in READONLY_PROPERTIES:
            return False
        return True

    def get_link_url(self, custom_property):
        return reverse(self.url, args=[self.table.kwargs['id'],
                                       http.urlquote(custom_property.key, '')])


class PropertiesTable(tables.DataTable):
    key = tables.Column('key', verbose_name=_('Key'))
    value = tables.Column('value', verbose_name=_('Value'))

    class Meta:
        name = "properties"
        verbose_name = _("Custom Properties")
        table_actions = (PropertyCreate, PropertyDelete)
        row_actions = (PropertyEdit, PropertyDelete)

    def get_object_id(self, datum):
        return datum.key

    def get_object_display(self, datum):
        return datum.key
