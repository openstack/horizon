# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

from django.template.defaultfilters import title
from django.template.loader import render_to_string

from horizon.utils import filters


def stack_info(stack, stack_image):
    stack.stack_status_desc = title(
        filters.replace_underscores(stack.stack_status))
    if stack.stack_status_reason:
        stack.stack_status_reason = title(
            filters.replace_underscores(stack.stack_status_reason)
        )
    context = {}
    context['stack'] = stack
    context['stack_image'] = stack_image
    return render_to_string('project/stacks/_stack_info.html',
                            context)


def resource_info(resource):
    resource.resource_status_desc = title(
        filters.replace_underscores(resource.resource_status)
    )
    if resource.resource_status_reason:
        resource.resource_status_reason = title(
            filters.replace_underscores(resource.resource_status_reason)
        )
    context = {}
    context['resource'] = resource
    return render_to_string('project/stacks/_resource_info.html',
                            context)
