# Copyright 2016 Hewlett Packard Enterprise Software, LLC
# All Rights Reserved.
#
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

"""
Allows Dynamic Theme Loading.
"""

import io
import os
import threading

import django
from django.conf import settings
from django.core.exceptions import SuspiciousFileOperation
from django.template.engine import Engine
from django.template.loaders.base import Loader as tLoaderCls
from django.utils._os import safe_join

if django.VERSION >= (1, 9):
    from django.template.exceptions import TemplateDoesNotExist
else:
    from django.template.base import TemplateDoesNotExist


# Local thread storage to retrieve the currently set theme
_local = threading.local()


# Get the themes from settings
def get_selectable_themes():
    return getattr(settings, 'SELECTABLE_THEMES', [])


# Get the themes from settings
def get_themes():
    return getattr(settings, 'AVAILABLE_THEMES',
                   [(get_default_theme(),
                     get_default_theme(),
                     os.path.join(get_theme_dir(), get_default_theme()))])


# Get the themes dir from settings
def get_theme_dir():
    return getattr(settings, 'THEME_COLLECTION_DIR', 'themes')


# Get the theme cookie name from settings
def get_theme_cookie_name():
    return getattr(settings, 'THEME_COOKIE_NAME', 'theme')


# Get the default theme
def get_default_theme():
    return getattr(settings, 'DEFAULT_THEME', 'default')


# Find the theme tuple
def find_theme(theme_name):
    for each_theme in get_themes():
        if theme_name == each_theme[0]:
            return each_theme

    return None


# Offline Context Generator
def offline_context():
    for theme in get_themes():
        base_context = \
            getattr(
                settings,
                'HORIZON_COMPRESS_OFFLINE_CONTEXT_BASE',
                {}
            ).copy()
        base_context['THEME'] = theme[0]
        base_context['THEME_DIR'] = get_theme_dir()
        yield base_context


# A piece of middleware that stores the theme cookie value into
# local thread storage so the template loader can access it
class ThemeMiddleware(object):
    """The Theme Middleware component.

    The custom template loaders
    don't have access to the request object, so we need to store
    the Cookie's theme value for use later in the Django chain.
    """

    def process_request(self, request):

        # Determine which theme the user has configured and store in local
        # thread storage so that it persists to the custom template loader
        try:
            _local.theme = request.COOKIES[get_theme_cookie_name()]
        except KeyError:
            _local.theme = get_default_theme()

    def process_response(self, request, response):
        try:
            delattr(_local, 'theme')
        except AttributeError:
            pass

        return response


class ThemeTemplateLoader(tLoaderCls):
    """Theme-aware template loader.

    Themes can contain template overrides, so we need to check the
    theme directory first, before loading any of the standard templates.
    """
    is_usable = True

    def get_template_sources(self, template_name):

        # If the cookie doesn't exist, set it to the default theme
        default_theme = get_default_theme()
        theme = getattr(_local, 'theme', default_theme)
        this_theme = find_theme(theme)

        # If the theme is not valid, check the default theme ...
        if not this_theme:
            this_theme = find_theme(get_default_theme())

            # If the theme is still not valid, then move along ...
            # these aren't the templates you are looking for
            if not this_theme:
                pass

        try:
            # To support themes residing outside of Django, use os.path.join to
            # avoid throwing a SuspiciousFileOperation and immediately exiting.
            template_path = os.path.join(
                getattr(
                    settings,
                    'ROOT_PATH',
                    os.path.abspath('openstack_dashboard')
                ),
                this_theme[2],
                'templates'
            )
            if not template_name.startswith('/'):
                try:
                    yield safe_join(template_path, template_name)
                except SuspiciousFileOperation:
                    yield os.path.join(
                        this_theme[2], 'templates', template_name
                    )
            elif template_path in template_name:
                yield template_name

        except UnicodeDecodeError:
            # The template dir name wasn't valid UTF-8.
            raise
        except ValueError:
            # The joined path was located outside of template_dir.
            pass

    def load_template_source(self, template_name, template_dirs=None):
        for path in self.get_template_sources(template_name):
            try:
                with io.open(path, encoding=settings.FILE_CHARSET) as file:
                    return file.read(), path
            except IOError:
                pass
        raise TemplateDoesNotExist(template_name)


e = Engine()
_loader = ThemeTemplateLoader(e)
