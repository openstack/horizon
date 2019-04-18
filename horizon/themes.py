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

import os
import threading

from django.conf import settings
from django.core.exceptions import SuspiciousFileOperation
from django.template.loaders import filesystem as filesystem_loader
from django.template import Origin
from django.utils._os import safe_join


# Local thread storage to retrieve the currently set theme
_local = threading.local()


# Get the themes from settings
def get_selectable_themes():
    return settings.SELECTABLE_THEMES


# Get the themes from settings
def get_themes():
    # TODO(amotoki): Consider how to define the default value
    return getattr(settings, 'AVAILABLE_THEMES',
                   [(get_default_theme(),
                     get_default_theme(),
                     os.path.join(get_theme_dir(), get_default_theme()))])


# Get the themes dir from settings
def get_theme_dir():
    return settings.THEME_COLLECTION_DIR


# Get the theme cookie name from settings
def get_theme_cookie_name():
    return settings.THEME_COOKIE_NAME


# Get the default theme
def get_default_theme():
    return settings.DEFAULT_THEME


# Find the theme tuple
def find_theme(theme_name):
    for each_theme in get_themes():
        if theme_name == each_theme[0]:
            return each_theme

    return None


# Offline Context Generator
def offline_context():
    for theme in get_themes():
        base_context = settings.HORIZON_COMPRESS_OFFLINE_CONTEXT_BASE.copy()
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

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        self.process_request(request)
        response = self.get_response(request)
        response = self.process_response(request, response)
        return response

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


class ThemeTemplateLoader(filesystem_loader.Loader):
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
            name = None
            if not template_name.startswith('/'):
                try:
                    name = safe_join(template_path, template_name)
                except SuspiciousFileOperation:
                    name = os.path.join(
                        this_theme[2], 'templates', template_name
                    )
            elif template_path in template_name:
                name = template_name

            if name:
                yield Origin(name=name,
                             template_name=template_name,
                             loader=self)
        # pylint: disable=try-except-raise
        except UnicodeDecodeError:
            # The template dir name wasn't valid UTF-8.
            raise
