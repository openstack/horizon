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

"""
Wrapper for loading templates from "templates" directories in panel modules.
"""

import os

from django.core.exceptions import SuspiciousFileOperation
from django.template.loaders import filesystem as filesystem_loader
from django.template import Origin
from django.utils._os import safe_join


# Set up a cache of the panel directories to search.
panel_template_dirs = {}


class TemplateLoader(filesystem_loader.Loader):

    def get_template_sources(self, template_name):
        bits = template_name.split('/', 2)
        if len(bits) == 3:
            dash_name, panel_name, remainder = bits
            key = os.path.join(dash_name, panel_name)
            if key in panel_template_dirs:
                template_dir = panel_template_dirs[key]
                try:
                    name = safe_join(template_dir, panel_name, remainder)
                    yield Origin(name=name,
                                 template_name=template_name,
                                 loader=self)
                # pylint: disable=try-except-raise
                except UnicodeDecodeError:
                    # The template dir name wasn't valid UTF-8.
                    raise
                except SuspiciousFileOperation:
                    # The joined path was located outside of this template_dir
                    # (it might be inside another one, so this isn't fatal).
                    pass
