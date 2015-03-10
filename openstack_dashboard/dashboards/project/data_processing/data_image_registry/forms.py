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

import json

from django.utils.translation import ugettext_lazy as _

from horizon import exceptions
from horizon import forms
from horizon import messages
from openstack_dashboard.api import glance
from openstack_dashboard.api import sahara as saharaclient


class ImageForm(forms.SelfHandlingForm):
    image_id = forms.CharField(widget=forms.HiddenInput())
    tags_list = forms.CharField(widget=forms.HiddenInput())
    user_name = forms.CharField(max_length=80, label=_("User Name"))
    description = forms.CharField(max_length=80,
                                  label=_("Description"),
                                  required=False,
                                  widget=forms.Textarea(attrs={'rows': 4}))

    def handle(self, request, data):
        try:
            image_id = data['image_id']
            user_name = data['user_name']
            desc = data['description']
            saharaclient.image_update(request, image_id, user_name, desc)

            image_tags = json.loads(data["tags_list"])
            saharaclient.image_tags_update(request, image_id, image_tags)
            updated_image = saharaclient.image_get(request, image_id)
            messages.success(request,
                             _("Successfully updated image."))
            return updated_image
        except Exception:
            exceptions.handle(request,
                              _("Failed to update image."))
            return False


class EditTagsForm(ImageForm):
    image_id = forms.CharField(widget=forms.HiddenInput())


class RegisterImageForm(ImageForm):
    image_id = forms.ChoiceField(label=_("Image"))

    def __init__(self, request, *args, **kwargs):
        super(RegisterImageForm, self).__init__(request, *args, **kwargs)
        self._populate_image_id_choices()

    def _populate_image_id_choices(self):
        images = self._get_available_images(self.request)
        choices = [(image.id, image.name)
                   for image in images
                   if image.properties.get("image_type", '') != "snapshot"]
        if choices:
            choices.insert(0, ("", _("Select Image")))
        else:
            choices.insert(0, ("", _("No images available.")))
        self.fields['image_id'].choices = choices

    def _get_images(self, request, filter):
        try:
            images, _more, _prev = (
                glance.image_list_detailed(request, filters=filter))
        except Exception:
            images = []
            exceptions.handle(request,
                              _("Unable to retrieve images with filter %s.") %
                              filter)
        return images

    def _get_public_images(self, request):
        filter = {"is_public": True,
                  "status": "active"}
        return self._get_images(request, filter)

    def _get_tenant_images(self, request):
        filter = {"owner": request.user.tenant_id,
                  "status": "active"}
        return self._get_images(request, filter)

    def _get_available_images(self, request):

        images = self._get_tenant_images(request)
        if request.user.is_superuser:
            images += self._get_public_images(request)

        final_images = []

        try:
            image_ids = set(img.id for img in saharaclient.image_list(request))
        except Exception:
            image_ids = set()
            exceptions.handle(request,
                              _("Unable to fetch available images."))

        for image in images:
            if (image not in final_images and
                    image.id not in image_ids and
                    image.container_format not in ('aki', 'ari')):
                final_images.append(image)
        return final_images
