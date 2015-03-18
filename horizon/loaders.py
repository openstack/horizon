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

import django
from django.conf import settings
from django.template.base import TemplateDoesNotExist  # noqa

if django.get_version() >= '1.8':
    from django.template.engine import Engine
    from django.template.loaders.base import Loader as tLoaderCls
else:
    from django.template.loader import BaseLoader as tLoaderCls  # noqa

from django.utils._os import safe_join  # noqa

# Set up a cache of the panel directories to search.
panel_template_dirs = {}


class TemplateLoader(tLoaderCls):
    is_usable = True

    def get_template_sources(self, template_name):
        bits = template_name.split('/', 2)
        if len(bits) == 3:
            dash_name, panel_name, remainder = bits
            key = os.path.join(dash_name, panel_name)
            if key in panel_template_dirs:
                template_dir = panel_template_dirs[key]
                try:
                    yield safe_join(template_dir, panel_name, remainder)
                except UnicodeDecodeError:
                    # The template dir name wasn't valid UTF-8.
                    raise
                except ValueError:
                    # The joined path was located outside of template_dir.
                    pass

    def load_template_source(self, template_name, template_dirs=None):
        for path in self.get_template_sources(template_name):
            try:
                with open(path) as file:
                    return (file.read().decode(settings.FILE_CHARSET), path)
            except IOError:
                pass
        raise TemplateDoesNotExist(template_name)


if django.get_version() >= '1.8':
    e = Engine()
    _loader = TemplateLoader(e)
else:
    _loader = TemplateLoader()
