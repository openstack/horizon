# Copyright 2015 IBM Corp.
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
"""API over the cinder service.
"""

from django.views import generic

from openstack_dashboard import api
from openstack_dashboard.api.rest import urls
from openstack_dashboard.api.rest import utils as rest_utils


CLIENT_KEYWORDS = {'marker', 'sort_dir', 'paginate'}


@urls.register
class Volumes(generic.View):
    """API for cinder volumes.
    """
    url_regex = r'cinder/volumes/$'

    @rest_utils.ajax()
    def get(self, request):
        """Get a detailed list of volumes associated with the current user's
        project.

        Example GET:
        http://localhost/api/cinder/volumes?paginate=true&sort_dir=asc

        If invoked as an admin, you may set the GET parameter "all_projects"
        to 'true' to return details for all projects.

        The following get parameters may be passed in the GET

        :param search_opts: includes options such as name, status, bootable
        :param paginate: If true will perform pagination based on settings.
        :param marker: Specifies the namespace of the last-seen image.
             The typical pattern of limit and marker is to make an
             initial limited request and then to use the last
             namespace from the response as the marker parameter
             in a subsequent limited request. With paginate, limit
             is automatically set.
        :param sort_dir: The sort direction ('asc' or 'desc').

        The listing result is an object with property "items".
        """

        if request.GET.get('all_projects') == 'true':
            result, has_more, has_prev = api.cinder.volume_list_paged(
                request,
                {'all_tenants': 1}
            )
        else:
            search_opts, kwargs = rest_utils.parse_filters_kwargs(
                request, CLIENT_KEYWORDS)
            result, has_more, has_prev = api.cinder.volume_list_paged(
                request,
                search_opts=search_opts, **kwargs
            )
        return {
            'items': [u.to_dict() for u in result],
            'has_more_data': has_more,
            'has_prev_data': has_prev
        }

    @rest_utils.ajax(data_required=True)
    def post(self, request):
        volume = api.cinder.volume_create(
            request,
            size=request.DATA['size'],
            name=request.DATA['name'],
            description=request.DATA['description'],
            volume_type=request.DATA['volume_type'],
            snapshot_id=request.DATA['snapshot_id'],
            metadata=request.DATA['metadata'],
            image_id=request.DATA['image_id'],
            availability_zone=request.DATA['availability_zone'],
            source_volid=request.DATA['source_volid']
        )

        return rest_utils.CreatedResponse(
            '/api/cinder/volumes/%s' % volume.id,
            volume.to_dict()
        )


@urls.register
class Volume(generic.View):
    """API for cinder volume.
    """
    url_regex = r'cinder/volumes/(?P<volume_id>[^/]+)/$'

    @rest_utils.ajax()
    def get(self, request, volume_id):
        """Get a single volume's details with the volume id.

        The following get parameters may be passed in the GET

        :param volume_id: the id of the volume

        The result is a volume object.
        """
        return api.cinder.volume_get(request, volume_id).to_dict()


@urls.register
class VolumeTypes(generic.View):
    """API for volume types.
    """
    url_regex = r'cinder/volumetypes/$'

    @rest_utils.ajax()
    def get(self, request):
        """Get a list of volume types.

        The listing result is an object with the property "items".
        """
        result = api.cinder.volume_type_list(request)
        return {'items': [api.cinder.VolumeType(u).to_dict() for u in result]}


@urls.register
class VolumeType(generic.View):
    """API for getting a volume type.
    """
    url_regex = r'cinder/volumetypes/(?P<volumetype_id>[^/]+)/$'

    @rest_utils.ajax()
    def get(self, request, volumetype_id):
        """Get a single volume type details with the volume type id.

        The following get parameters may be passed in the GET

        :param volumetype_id: the id of the volume type

        If 'default' is passed as the volumetype_id then
        it returns the default volumetype

        The result is a volume type object.
        """
        if volumetype_id == 'default':
            volumetype = api.cinder.volume_type_default(request)
        else:
            volumetype = api.cinder.volume_type_get(request, volumetype_id)

        return api.cinder.VolumeType(volumetype).to_dict()


@urls.register
class VolumeSnapshots(generic.View):
    """API for cinder volume snapshots.
    """
    url_regex = r'cinder/volumesnapshots/$'

    @rest_utils.ajax()
    def get(self, request):
        """Get a detailed list of volume snapshots associated with the current
        user's project.

        The listing result is an object with property "items".
        """
        result = api.cinder.volume_snapshot_list(
            request,
            search_opts=rest_utils.parse_filters_kwargs(request)[0]
        )
        return {'items': [u.to_dict() for u in result]}


@urls.register
class Extensions(generic.View):
    """API for cinder extensions.
    """
    url_regex = r'cinder/extensions/$'

    @rest_utils.ajax()
    def get(self, request):
        """Get a list of extensions.

        The listing result is an object with property "items". Each item is
        an extension.

        Example GET:
        http://localhost/api/cinder/extensions
        """
        result = api.cinder.list_extensions(request)
        return {'items': [{
            'alias': e.alias,
            'description': e.description,
            'links': e.links,
            'name': e.name,
            'namespace': e.namespace,
            'updated': e.updated

        } for e in result]}


@urls.register
class QoSSpecs(generic.View):
    url_regex = r'cinder/qosspecs/$'

    @rest_utils.ajax()
    def get(self, request):
        result = api.cinder.qos_specs_list(request)
        return {'items': [u.to_dict() for u in result]}


@urls.register
class TenantAbsoluteLimits(generic.View):
    url_regex = r'cinder/tenantabsolutelimits/$'

    @rest_utils.ajax()
    def get(self, request):
        return api.cinder.tenant_absolute_limits(request)


@urls.register
class Services(generic.View):
    """API for cinder services.
    """
    url_regex = r'cinder/services/$'

    @rest_utils.ajax()
    def get(self, request):
        """Get a list of cinder services.
        Will return HTTP 501 status code if the service_list extension is
        not supported.
        """
        if api.base.is_service_enabled(request, 'volume') and \
           api.cinder.extension_supported(request, 'Services'):
            result = api.cinder.service_list(request)
            return {'items': [{
                'binary': u.binary,
                'host': u.host,
                'zone': u.zone,
                'updated_at': u.updated_at,
                'status': u.status,
                'state': u.state,
                'id': idx + 1
            } for idx, u in enumerate(result)]}
        else:
            raise rest_utils.AjaxError(501, '')
