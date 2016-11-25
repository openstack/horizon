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

import six

from django.conf import settings
from django.utils.module_loading import import_string


def import_object(name_or_object):
    if isinstance(name_or_object, six.string_types):
        return import_string(name_or_object)
    return name_or_object


def import_setting(name):
    """Imports an object specified either directly or as a module path."""
    value = getattr(settings, name, None)
    return import_object(value)
