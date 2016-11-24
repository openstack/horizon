# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

from django.core import validators
from django.utils.translation import ugettext_lazy as _

from openstack_dashboard.api import swift


no_slash_validator = validators.RegexValidator(r'^(?u)[^/]+$',
                                               _("Slash is not an allowed "
                                                 "character."),
                                               code="noslash")
no_begin_or_end_slash = validators.RegexValidator(r'^[^\/](?u).+[^\/]$',
                                                  _("Slash is not allowed at "
                                                    "the beginning or end of "
                                                    "your string."),
                                                  code="nobeginorendslash")


def wrap_delimiter(name):
    if name and not name.endswith(swift.FOLDER_DELIMITER):
        return name + swift.FOLDER_DELIMITER
    return name
