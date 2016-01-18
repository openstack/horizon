# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

import django
from django import template
from django.template import defaultfilters
from django.utils import safestring

if django.VERSION >= (1, 9):
    register = template.Library()
else:
    register = template.base.Library()


@register.filter(is_safe=True)
@defaultfilters.stringfilter
def shellfilter(value):
    """Replace HTML chars for shell usage."""
    replacements = {'\\': '\\\\',
                    '`': '\`',
                    "'": "\\'",
                    '"': '\\"'}
    for search, repl in replacements.items():
        value = value.replace(search, repl)
    return safestring.mark_safe(value)
