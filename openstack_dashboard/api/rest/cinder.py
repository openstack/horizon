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


def _parse_filters(request):
    """Extract REST filter parameters from the request GET args.

    We iterate like this so we avoid Django GET's odd behaviour of
    handing a list-of-param through some QueryDict accesses.
    """
    filters = {}
    for param in request.GET:
        filters[param] = request.GET[param]
    return filters


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
                search_opts=_parse_filters(request)
            )
        return {'items': [u.to_dict() for u in result]}


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
            search_opts=_parse_filters(request)
        )
        return {'items': [u.to_dict() for u in result]}
