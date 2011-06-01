# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright 2010 United States Government as represented by the
# Administrator of the National Aeronautics and Space Administration.
# All Rights Reserved.
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
"""
Template tags for gathering contextual region data.
"""

from django import template
from django_openstack.nova import shortcuts

register = template.Library()


class RegionsNode(template.Node):
    def render(self, context):
        # Store region info in template context.
        context['current_region'] = \
                shortcuts.get_current_region(context['request'])
        context['regions'] = shortcuts.get_all_regions()
        return ''


@register.tag
def load_regions(parser, token):
    return RegionsNode()
