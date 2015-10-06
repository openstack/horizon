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
"""API for the heat service.
"""

from django.views import generic

from openstack_dashboard import api
from openstack_dashboard.api.rest import urls
from openstack_dashboard.api.rest import utils as rest_utils


@urls.register
class Validate(generic.View):
    """API for validating a template
    """
    url_regex = r'heat/validate/$'

    @rest_utils.ajax()
    def post(self, request):
        """Validate a template

        The following parameters may be passed in the POST
        application/json object. The parameters are:
        request:

        :param template_url: The template to validate
        """
        return api.heat.template_validate(request, **(request.DATA))


@urls.register
class Services(generic.View):
    """API for heat services.
    """
    url_regex = r'heat/services/$'

    @rest_utils.ajax()
    def get(self, request):
        """Get a list of heat services.
        """
        if api.base.is_service_enabled(request, 'orchestration'):
            result = api.heat.service_list(request)
            return {'items': [u.to_dict() for u in result]}
        else:
            raise rest_utils.AjaxError(501, '')
