# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

from django.utils.translation import ugettext_lazy as _

from horizon import exceptions
from horizon.templatetags import sizeformat

from openstack_dashboard.api import glance


def get_available_images(request, project_id=None, images_cache=None):
    """Returns a list of images that are public or owned by the given
    project_id. If project_id is not specified, only public images
    are returned.

    :param images_cache: An optional dict-like object in which to
     cache public and per-project id image metadata.

    """
    if images_cache is None:
        images_cache = {}
    public_images = images_cache.get('public_images', [])
    images_by_project = images_cache.get('images_by_project', {})
    if 'public_images' not in images_cache:
        public = {"is_public": True,
                  "status": "active"}
        try:
            images, _more, _prev = glance.image_list_detailed(
                request, filters=public)
            [public_images.append(image) for image in images]
            images_cache['public_images'] = public_images
        except Exception:
            exceptions.handle(request,
                              _("Unable to retrieve public images."))

    # Preempt if we don't have a project_id yet.
    if project_id is None:
        images_by_project[project_id] = []

    if project_id not in images_by_project:
        owner = {"property-owner_id": project_id,
                 "status": "active"}
        try:
            owned_images, _more, _prev = glance.image_list_detailed(
                request, filters=owner)
            images_by_project[project_id] = owned_images
        except Exception:
            owned_images = []
            exceptions.handle(request,
                              _("Unable to retrieve images for "
                                "the current project."))
    else:
        owned_images = images_by_project[project_id]

    if 'images_by_project' not in images_cache:
        images_cache['images_by_project'] = images_by_project

    images = owned_images + public_images

    # Remove duplicate images
    image_ids = []
    final_images = []
    for image in images:
        if image.id not in image_ids:
            image_ids.append(image.id)
            final_images.append(image)
    return [image for image in final_images
            if image.container_format not in ('aki', 'ari')]


def image_field_data(request, include_empty_option=False):
    """Returns a list of tuples of all images.

    Generates a sorted list of images available. And returns a list of
    (id, name) tuples.

    :param request: django http request object
    :param include_empty_option: flag to include a empty tuple in the front of
    the list
    :return: list of (id, name) tuples
    """
    try:
        images = get_available_images(request, request.user.project_id)
    except Exception:
        exceptions.handle(request, _('Unable to retrieve images'))
    images.sort(key=lambda c: c.name)
    images_list = [('', _('Select Image'))]
    for image in images:
        image_label = u"{} ({})".format(image.name,
                                        sizeformat.diskgbformat(image.size))
        images_list.append((image.id, image_label))

    if not images:
        return [("", _("No images available")), ]

    return images_list
