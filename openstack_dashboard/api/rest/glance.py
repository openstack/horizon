
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
"""API for the glance service.
"""

from itertools import izip
from django.views import generic

from openstack_dashboard import api
from openstack_dashboard.api.rest import utils as rest_utils
from openstack_dashboard.api.rest import urls


CLIENT_KEYWORDS = {'resource_type', 'marker', 'sort_dir', 'sort_key', 'paginate'}


@urls.register
class Image(generic.View):
    """API for retrieving a single image
    """
    url_regex = r'glance/images/(?P<image_id>.+|default)$'

    @rest_utils.ajax()
    def get(self, request, image_id):
        """Get a specific image

        http://localhost/api/glance/images/cc758c90-3d98-4ea1-af44-aab405c9c915
        """
        return api.glance.image_get(request, image_id).to_dict()


@urls.register
class Images(generic.View):
    """API for Glance images.
    """
    url_regex = r'glance/images/$'

    @rest_utils.ajax()
    def get(self, request):
        """Get a list of images.

        The listing result is an object with property "items". Each item is
        an image.

        Example GET:
        http://localhost/api/glance/images?sort_dir=desc&sort_key=name&name=cirros-0.3.2-x86_64-uec  #flake8: noqa

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
        separate work stream: https://review.openstack.org/#/c/150084/
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


@urls.register
class MetadefsNamespaces(generic.View):
    """API for Single Glance Metadata Definitions.

       http://docs.openstack.org/developer/glance/metadefs-concepts.html
    """
    url_regex = r'glance/metadefs/namespaces/$'

    @rest_utils.ajax()
    def get(self, request):
        """Get a list of metadata definition namespaces.

        The listing result is an object with property "items". Each item is
        a namespace.

        Example GET:
        http://localhost/api/glance/metadefs/namespaces?resource_types=OS::Nova::Flavor&sort_dir=desc&marker=OS::Compute::Watchdog&paginate=False&sort_key=namespace  #flake8: noqa

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
