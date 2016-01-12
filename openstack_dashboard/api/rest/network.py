
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
"""API for the network abstraction APIs.
"""

from django.views import generic

from openstack_dashboard import api
from openstack_dashboard.api.rest import urls
from openstack_dashboard.api.rest import utils as rest_utils


@urls.register
class SecurityGroups(generic.View):
    """API for Network Abstraction

    Handles differences between Nova and Neutron.
    """
    url_regex = r'network/securitygroups/$'

    @rest_utils.ajax()
    def get(self, request):
        """Get a list of security groups.

        The listing result is an object with property "items". Each item is
        a security group.

        Example GET:
        http://localhost/api/network/securitygroups
        """

        security_groups = api.network.security_group_list(request)

        return {'items': [sg.to_dict() for sg in security_groups]}
