# Copyright 2012 United States Government as represented by the
# Administrator of the National Aeronautics and Space Administration.
# All Rights Reserved.
#
# Copyright 2012 Nebula, Inc.
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
Template tags for parsing date strings.
"""

from datetime import datetime

from django import template
from django.utils import timezone


register = template.Library()


class ParseDateNode(template.Node):
    def render(self, datestring):
        """Parses a date-like string into a timezone aware Python datetime."""
        formats = ["%Y-%m-%dT%H:%M:%S.%f", "%Y-%m-%d %H:%M:%S.%f",
                   "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d %H:%M:%S"]
        if datestring:
            for format in formats:
                try:
                    parsed = datetime.strptime(datestring, format)
                    if not timezone.is_aware(parsed):
                        parsed = timezone.make_aware(parsed, timezone.utc)
                    return parsed
                except Exception:
                    pass
        return None


@register.filter(name='parse_date')
def parse_date(value):
    return ParseDateNode().render(value)
