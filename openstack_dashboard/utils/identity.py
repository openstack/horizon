# Copyright 2017 Red Hat, Inc.
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

from openstack_dashboard import api


def get_domain_id_for_operation(request):
    """Get the ID of the domain in which the current operation should happen.

    If the user has a domain context set, use that, otherwise use the user's
    effective domain.
    """

    domain_context = request.session.get('domain_context')
    if domain_context:
        return domain_context
    return api.keystone.get_effective_domain_id(request)
