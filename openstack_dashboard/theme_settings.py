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


import logging
import os


def get_theme_static_dirs(available_themes, collection_dir, root):
    static_dirs = []
    # Collect and expose the themes that have been configured
    for theme in available_themes:
        theme_name, theme_label, theme_path = theme
        theme_url = os.path.join(collection_dir, theme_name)
        theme_path = os.path.join(root, theme_path)
        if os.path.exists(os.path.join(theme_path, 'static')):
            # Only expose the subdirectory 'static' if it exists from a custom
            # theme, allowing other logic to live with a theme that we might
            # not want to expose statically
            theme_path = os.path.join(theme_path, 'static')

        static_dirs.append(
            (theme_url, theme_path),
        )

    return static_dirs


def get_available_themes(available_themes, default_theme, selectable_themes):
    new_theme_list = []
    # We can only support one path at a time, because of static file
    # collection.
    default_theme_ndx = -1
    for ndx, each_theme in enumerate(available_themes):
        # Make sure that DEFAULT_THEME is configured for use
        if each_theme[0] == default_theme:
            default_theme_ndx = ndx

        new_theme_list.append(each_theme)

    # If default is not configured, we have to set one,
    # just grab the first theme
    if default_theme_ndx == -1:
        default_theme = available_themes[0][0]

    if selectable_themes is None:
        selectable_themes = new_theme_list

    if default_theme not in [x[0] for x in selectable_themes]:
        default_theme = selectable_themes[0][0]
        logging.warning("Your DEFAULT_THEME is not configured in your "
                        "selectable themes, therefore using %s as your "
                        "default theme.", default_theme)

    return new_theme_list, selectable_themes, default_theme
