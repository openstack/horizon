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

from openstack_dashboard.api import glance


def get_available_images(request, project_id=None, images_cache=None):
    """Returns a list of available images

    Returns a list of images that are public, shared, community or owned by
    the given project_id. If project_id is not specified, only public and
    community images are returned.

    :param images_cache: An optional dict-like object in which to
    cache public and per-project id image metadata.
    """

    if images_cache is None:
        images_cache = {}
    public_images = images_cache.get('public_images', [])
    community_images = images_cache.get('community_images', [])
    images_by_project = images_cache.get('images_by_project', {})
    shared_images = images_cache.get('shared_images', [])
    if 'public_images' not in images_cache:
        public = {"is_public": True,
                  "status": "active"}
        try:
            images, _more, _prev = glance.image_list_detailed(
                request, filters=public)
            public_images += images
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

    if 'community_images' not in images_cache:
        community = {"visibility": "community",
                     "status": "active"}
        try:
            images, _more, _prev = glance.image_list_detailed(
                request, filters=community)
            community_images += images
            images_cache['community_images'] = community_images
        except Exception:
            exceptions.handle(request,
                              _("Unable to retrieve community images."))

    if 'shared_images' not in images_cache:
        shared = {"visibility": "shared",
                  "status": "active"}
        try:
            shared_images, _more, _prev = \
                glance.image_list_detailed(request, filters=shared)
            images_cache['shared_images'] = shared_images
        except Exception:
            exceptions.handle(request,
                              _("Unable to retrieve shared images."))

    if 'images_by_project' not in images_cache:
        images_cache['images_by_project'] = images_by_project

    images = owned_images + public_images + community_images + shared_images

    image_ids = []
    final_images = []
    for image in images:
        if image.id not in image_ids and \
                image.container_format not in ('aki', 'ari'):
            image_ids.append(image.id)
            final_images.append(image)
    return final_images
