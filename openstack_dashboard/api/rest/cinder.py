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
from openstack_dashboard.api.rest import utils as rest_utils

from openstack_dashboard.api.rest import urls


@urls.register
class Volumes(generic.View):
    """API for cinder volumes.
    """
    url_regex = r'cinder/volumes/$'

    @rest_utils.ajax()
    def get(self, request):
        """Get a detailed list of volumes associated with the current user's
        project.

        If invoked as an admin, you may set the GET parameter "all_projects"
        to 'true'.

        The following get parameters may be passed in the GET

        :param search_opts includes options such as name, status, bootable

        The listing result is an object with property "items".
        """
        # TODO(clu_): when v2 pagination stuff in Cinder API merges
        # (https://review.openstack.org/#/c/118450), handle here accordingly

        if request.GET.get('all_projects') == 'true':
            result = api.cinder.volume_list(request, {'all_tenants': 1})
        else:
            result = api.cinder.volume_list(
                request,
                search_opts=rest_utils.parse_filters_kwargs(request)[0]
            )
        return {'items': [u.to_dict() for u in result]}


@urls.register
class Volume(generic.View):
    """API for cinder volume.
    """
    url_regex = r'cinder/volumes/(?P<volume_id>[^/]+)/$'

    @rest_utils.ajax()
    def get(self, request, volume_id):
        """Get a single volume's details with the volume id.

        The following get parameters may be passed in the GET

        :param volume_id the id of the volume

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

        :param volumetype_id the id of the volume type

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
