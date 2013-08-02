"""
Wrapper for loading templates from "templates" directories in panel modules.
"""

import os

from django.conf import settings  # noqa
from django.template.base import TemplateDoesNotExist  # noqa
from django.template.loader import BaseLoader  # noqa
from django.utils._os import safe_join  # noqa

# Set up a cache of the panel directories to search.
panel_template_dirs = {}


class TemplateLoader(BaseLoader):
    is_usable = True

    def get_template_sources(self, template_name):
        bits = template_name.split(os.path.sep, 2)
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
                file = open(path)
                try:
                    return (file.read().decode(settings.FILE_CHARSET), path)
                finally:
                    file.close()
            except IOError:
                pass
        raise TemplateDoesNotExist(template_name)


_loader = TemplateLoader()
