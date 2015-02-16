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


from django.conf import settings


def check(actions, request, target=None):
    """Wrapper of the configurable policy method."""

    policy_check = getattr(settings, "POLICY_CHECK_FUNCTION", None)

    if policy_check:
        return policy_check(actions, request, target)

    return True


class PolicyTargetMixin(object):
    """Mixin that adds the get_policy_target function

    policy_target_attrs - a tuple of tuples which defines
        the relationship between attributes in the policy
        target dict and attributes in the passed datum object.
        policy_target_attrs can be overwritten by sub-classes
        which do not use the default, so they can neatly define
        their policy target information, without overriding the
        entire get_policy_target function.
    """

    policy_target_attrs = (("project_id", "tenant_id"),
                           ("user_id", "user_id"),
                           ("domain_id", "domain_id"))

    def get_policy_target(self, request, datum=None):
        policy_target = {}
        for policy_attr, datum_attr in self.policy_target_attrs:
            if datum:
                policy_target[policy_attr] = getattr(datum, datum_attr, None)
            else:
                policy_target[policy_attr] = None
        return policy_target
