# Copyright 2015, Hewlett-Packard Development Company, L.P.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""API for the glance service."""

from django import forms
from django.views.decorators.csrf import csrf_exempt
from django.views import generic
from six.moves import zip as izip

from openstack_dashboard import api
from openstack_dashboard.api.rest import urls
from openstack_dashboard.api.rest import utils as rest_utils

CLIENT_KEYWORDS = {'resource_type', 'marker',
                   'sort_dir', 'sort_key', 'paginate'}


@urls.register
class Version(generic.View):
    """API for active glance version."""
    url_regex = r'glance/version/$'

    @rest_utils.ajax()
    def get(self, request):
        """Get active glance version."""
        return {'version': str(api.glance.get_version())}


@urls.register
class Image(generic.View):
    """API for retrieving a single image"""
    url_regex = r'glance/images/(?P<image_id>[^/]+|default)/$'

    @rest_utils.ajax()
    def get(self, request, image_id):
        """Get a specific image

        http://localhost/api/glance/images/cc758c90-3d98-4ea1-af44-aab405c9c915
        """
        image = api.glance.image_get(request, image_id)
        return image.to_dict(show_ext_attrs=True)

    @rest_utils.ajax(data_required=True)
    def patch(self, request, image_id):
        """Update a specific image

        Update an Image using the parameters supplied in the POST
        application/json object. The parameters are:

        :param name: (required) the name to give the image
        :param description: (optional) description of the image
        :param disk_format: (required) format of the image
        :param kernel: (optional) kernel to use for the image
        :param ramdisk: (optional) Ramdisk to use for the image
        :param architecture: (optional) the Architecture of the image
        :param min_disk: (optional) the minimum disk size
             for the image to boot with
        :param min_ram: (optional) the minimum ram for the image to boot with
        :param visibility: (required) takes 'public', 'shared', 'private' and
             'community'
        :param protected: (required) true if the image is protected

        Any parameters not listed above will be assigned as custom properties
        for the image.

        http://localhost/api/glance/images/cc758c90-3d98-4ea1-af44-aab405c9c915

        """
        meta = _create_image_metadata(request.DATA)

        api.glance.image_update(request, image_id, **meta)

    @rest_utils.ajax()
    def delete(self, request, image_id):
        """Delete a specific image

        DELETE http://localhost/api/glance/images/<image_id>
        """
        api.glance.image_delete(request, image_id)


@urls.register
class ImageProperties(generic.View):
    """API for retrieving only a custom properties of single image."""
    url_regex = r'glance/images/(?P<image_id>[^/]+)/properties/'

    @rest_utils.ajax()
    def get(self, request, image_id):
        """Get custom properties of specific image."""
        return api.glance.image_get(request, image_id).properties

    @rest_utils.ajax(data_required=True)
    def patch(self, request, image_id):
        """Update custom properties of specific image.

        This method returns HTTP 204 (no content) on success.
        """
        if "os_hidden" in request.DATA['updated']:
            request.DATA['updated']['os_hidden'] = (
                request.DATA['updated']['os_hidden'] == "true")
        api.glance.image_update_properties(
            request, image_id, request.DATA.get('removed'),
            **request.DATA['updated']
        )


class UploadObjectForm(forms.Form):
    data = forms.FileField(required=False)


@urls.register
class Images(generic.View):
    """API for Glance images."""
    url_regex = r'glance/images/$'

    @rest_utils.ajax()
    def get(self, request):
        """Get a list of images.

        The listing result is an object with property "items". Each item is
        an image.

        Example GET:
        http://localhost/api/glance/images?sort_dir=desc&sort_key=name&name=cirros-0.3.2-x86_64-uec

        The following get parameters may be passed in the GET
        request:

        :param paginate: If true will perform pagination based on settings.
        :param marker: Specifies the namespace of the last-seen image.
             The typical pattern of limit and marker is to make an
             initial limited request and then to use the last
             namespace from the response as the marker parameter
             in a subsequent limited request. With paginate, limit
             is automatically set.
        :param sort_dir: The sort direction ('asc' or 'desc').
        :param sort_key: The field to sort on (for example, 'created_at').
             Default is created_at.

        Any additional request parameters will be passed through the API as
        filters. There are v1/v2 complications which are being addressed as a
        separate work stream: https://review.opendev.org/#/c/150084/
        """

        filters, kwargs = rest_utils.parse_filters_kwargs(request,
                                                          CLIENT_KEYWORDS)

        images, has_more_data, has_prev_data = api.glance.image_list_detailed(
            request, filters=filters, **kwargs)

        return {
            'items': [i.to_dict() for i in images],
            'has_more_data': has_more_data,
            'has_prev_data': has_prev_data,
        }

    # note: not an AJAX request - the body will be raw file content mixed with
    # metadata
    @rest_utils.post2data
    @csrf_exempt
    def post(self, request):
        form = UploadObjectForm(request.DATA, request.FILES)
        if not form.is_valid():
            raise rest_utils.AjaxError(500, 'Invalid request')

        data = form.clean()
        meta = _create_image_metadata(request.DATA)
        meta['data'] = data['data']

        image = api.glance.image_create(request, **meta)
        return rest_utils.CreatedResponse(
            '/api/glance/images/%s' % image.name,
            image.to_dict()
        )

    @rest_utils.ajax(data_required=True)
    def put(self, request):
        """Create an Image.

        Create an Image using the parameters supplied in the POST
        application/json object. The parameters are:

        :param name: the name to give the image
        :param description: (optional) description of the image
        :param source_type: (required) source type.
             current only 'url' is supported
        :param image_url: (required) URL to get the image
        :param disk_format: (required) format of the image
        :param kernel: (optional) kernel to use for the image
        :param ramdisk: (optional) Ramdisk to use for the image
        :param architecture: (optional) the Architecture of the image
        :param min_disk: (optional) the minimum disk size
             for the image to boot with
        :param min_ram: (optional) the minimum ram for the image to boot with
        :param visibility: (required) takes 'public', 'private', 'shared', and
             'community'
        :param protected: (required) true if the image is protected
        :param import_data: (optional) true to copy the image data
            to the image service or use it from the current location

        Any parameters not listed above will be assigned as custom properties
        for the image.

        This returns the new image object on success.
        """
        meta = _create_image_metadata(request.DATA)

        if request.DATA.get('image_url'):
            if request.DATA.get('import_data'):
                meta['copy_from'] = request.DATA.get('image_url')
            else:
                meta['location'] = request.DATA.get('image_url')
        else:
            meta['data'] = request.DATA.get('data')

        image = api.glance.image_create(request, **meta)
        return rest_utils.CreatedResponse(
            '/api/glance/images/%s' % image.name,
            image.to_dict()
        )


@urls.register
class MetadefsNamespaces(generic.View):
    """API for Single Glance Metadata Definitions.

       https://docs.openstack.org/glance/latest/user/metadefs-concepts.html
    """
    url_regex = r'glance/metadefs/namespaces/$'

    @rest_utils.ajax()
    def get(self, request):
        """Get a list of metadata definition namespaces.

        The listing result is an object with property "items". Each item is
        a namespace.

        Example GET:
        http://localhost/api/glance/metadefs/namespaces?resource_types=OS::Nova::Flavor&sort_dir=desc&marker=OS::Compute::Watchdog&paginate=False&sort_key=namespace

        The following get parameters may be passed in the GET
        request:

        :param resource_type: Namespace resource type.
            If specified returned namespace properties will have prefixes
            proper for selected resource type.
        :param paginate: If true will perform pagination based on settings.
        :param marker: Specifies the namespace of the last-seen namespace.
             The typical pattern of limit and marker is to make an
             initial limited request and then to use the last
             namespace from the response as the marker parameter
             in a subsequent limited request. With paginate, limit
             is automatically set.
        :param sort_dir: The sort direction ('asc' or 'desc').
        :param sort_key: The field to sort on (for example, 'created_at').
             Default is namespace. The way base namespaces are loaded into
             glance typically at first deployment is done in a single
             transaction giving them a potentially unpredictable sort result
             when using create_at.

        Any additional request parameters will be passed through the API as
        filters.
        """

        filters, kwargs = rest_utils.parse_filters_kwargs(
            request, CLIENT_KEYWORDS
        )

        names = ('items', 'has_more_data', 'has_prev_data')
        return dict(izip(names, api.glance.metadefs_namespace_full_list(
            request, filters=filters, **kwargs
        )))


@urls.register
class MetadefsResourceTypesList(generic.View):
    """API for getting Metadata Definitions Resource Types List.

       https://docs.openstack.org/glance/latest/user/metadefs-concepts.html
    """
    url_regex = r'glance/metadefs/resourcetypes/$'

    @rest_utils.ajax()
    def get(self, request):
        """Get Metadata definitions resource types list.

        The listing result is an object with property "items". Each item is
        a resource type.

        Example GET:
        http://localhost/api/glance/resourcetypes/

        Any request parameters will be passed through the API as filters.
        """
        return {
            'items': [resource_type for resource_type in
                      api.glance.metadefs_resource_types_list(request)]
        }


def _create_image_metadata(data):
    # In Angular implementation we use 'visibility' field only and
    # 'is_public' field is not used when creating/updating metadata.
    # However, the previous 'is_public' value is sent in a request.
    # We drop it here before passing it to create_image_metadata.
    if 'is_public' in data:
        del data['is_public']
    try:
        return api.glance.create_image_metadata(data)
    except KeyError as e:
        raise rest_utils.AjaxError(400, e.args[0])
