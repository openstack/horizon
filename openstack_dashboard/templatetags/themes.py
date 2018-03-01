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

from __future__ import absolute_import

import os

from six.moves.urllib.request import pathname2url

from django.conf import settings
from django.contrib.staticfiles.storage import staticfiles_storage
from django import template

from horizon import themes as hz_themes

register = template.Library()


def get_theme(request):

    this_theme = hz_themes.get_default_theme()
    try:
        theme = request.COOKIES[hz_themes.get_theme_cookie_name()]
        for each_theme in hz_themes.get_themes():
            if theme == each_theme[0]:
                this_theme = each_theme[0]
    except KeyError:
        pass

    return this_theme


def find_asset(theme, asset):

    theme_path = ''
    for name, label, path in hz_themes.get_themes():
        if theme == name:
            theme_path = path

    theme_path = os.path.join(settings.ROOT_PATH, theme_path)

    # If there is a 'static' subdir of the theme, then use
    # that as the theme's asset root path
    static_path = os.path.join(theme_path, 'static')
    if os.path.exists(static_path):
        theme_path = static_path

    # The full path to the asset requested
    asset_path = os.path.join(theme_path, asset)
    if os.path.exists(asset_path):
        return_path = os.path.join(hz_themes.get_theme_dir(), theme, asset)
    else:
        return_path = os.path.join('dashboard', asset)

    return staticfiles_storage.url(pathname2url(return_path))


@register.simple_tag()
def themes():
    return hz_themes.get_selectable_themes()


@register.simple_tag()
def theme_cookie():
    return hz_themes.get_theme_cookie_name()


@register.simple_tag()
def theme_dir():
    return hz_themes.get_theme_dir()


@register.simple_tag(takes_context=True)
def current_theme(context):
    return get_theme(context.request)


@register.simple_tag(takes_context=True)
def themable_asset(context, asset):
    return find_asset(get_theme(context.request), asset)
