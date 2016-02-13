#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

from django.views import generic

from openstack_dashboard.api.rest import urls
from openstack_dashboard.api.rest import utils as rest_utils
from openstack_dashboard import policy


@urls.register
class Policy(generic.View):
    '''API for interacting with the policy engine.'''

    url_regex = r'policy/$'

    @rest_utils.ajax(data_required=True)
    def post(self, request):
        '''Check policy rules.

        Check the group of policy rules supplied in the POST
        application/json object. The policy target, if specified will also be
        passed in to the policy check method as well.

        The action returns an object with one key: "allowed" and the value
        is the result of the policy check, True or False.
        '''

        rules = []
        try:
            rules_in = request.DATA['rules']
            rules = tuple([tuple(rule) for rule in rules_in])
        except Exception:
            raise rest_utils.AjaxError(400, 'unexpected parameter format')

        policy_target = request.DATA.get('target') or {}

        result = policy.check(rules, request, policy_target)

        return {"allowed": result}
