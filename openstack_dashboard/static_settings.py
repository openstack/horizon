#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

"""
This file contains configuration for the locations of all the static file
libraries, such as JavaScript and CSS libraries. Packagers for individual
distributions can edit or replace this file, in order to change the paths
to match their distribution's standards.
"""

import os

import xstatic.main
import xstatic.pkg.angular
import xstatic.pkg.angular_bootstrap
import xstatic.pkg.angular_fileupload
import xstatic.pkg.angular_gettext
import xstatic.pkg.angular_lrdragndrop
import xstatic.pkg.angular_schema_form
import xstatic.pkg.angular_smart_table
import xstatic.pkg.bootstrap_datepicker
import xstatic.pkg.bootstrap_scss
import xstatic.pkg.bootswatch
import xstatic.pkg.d3
import xstatic.pkg.font_awesome
import xstatic.pkg.hogan
import xstatic.pkg.jasmine
import xstatic.pkg.jquery
import xstatic.pkg.jquery_migrate
import xstatic.pkg.jquery_quicksearch
import xstatic.pkg.jquery_tablesorter
import xstatic.pkg.jquery_ui
import xstatic.pkg.jsencrypt
import xstatic.pkg.mdi
import xstatic.pkg.objectpath
import xstatic.pkg.rickshaw
import xstatic.pkg.roboto_fontface
import xstatic.pkg.spin
import xstatic.pkg.termjs
import xstatic.pkg.tv4

from horizon.utils import file_discovery

from openstack_dashboard import theme_settings


def get_staticfiles_dirs(webroot='/'):
    STATICFILES_DIRS = [
        ('horizon/lib/angular',
            xstatic.main.XStatic(xstatic.pkg.angular,
                                 root_url=webroot).base_dir),
        ('horizon/lib/angular',
            xstatic.main.XStatic(xstatic.pkg.angular_bootstrap,
                                 root_url=webroot).base_dir),
        ('horizon/lib/angular',
            xstatic.main.XStatic(xstatic.pkg.angular_fileupload,
                                 root_url=webroot).base_dir),
        ('horizon/lib/angular',
            xstatic.main.XStatic(xstatic.pkg.angular_gettext,
                                 root_url=webroot).base_dir),
        ('horizon/lib/angular',
            xstatic.main.XStatic(xstatic.pkg.angular_lrdragndrop,
                                 root_url=webroot).base_dir),
        ('horizon/lib/angular',
            xstatic.main.XStatic(xstatic.pkg.angular_schema_form,
                                 root_url=webroot).base_dir),
        ('horizon/lib/angular',
            xstatic.main.XStatic(xstatic.pkg.angular_smart_table,
                                 root_url=webroot).base_dir),
        ('horizon/lib/bootstrap_datepicker',
            xstatic.main.XStatic(xstatic.pkg.bootstrap_datepicker,
                                 root_url=webroot).base_dir),
        ('bootstrap',
            xstatic.main.XStatic(xstatic.pkg.bootstrap_scss,
                                 root_url=webroot).base_dir),
        ('horizon/lib/bootswatch',
         xstatic.main.XStatic(xstatic.pkg.bootswatch,
                              root_url=webroot).base_dir),
        ('horizon/lib',
            xstatic.main.XStatic(xstatic.pkg.d3,
                                 root_url=webroot).base_dir),
        ('horizon/lib',
            xstatic.main.XStatic(xstatic.pkg.hogan,
                                 root_url=webroot).base_dir),
        ('horizon/lib/font-awesome',
            xstatic.main.XStatic(xstatic.pkg.font_awesome,
                                 root_url=webroot).base_dir),
        ('horizon/lib/jasmine',
            xstatic.main.XStatic(xstatic.pkg.jasmine,
                                 root_url=webroot).base_dir),
        ('horizon/lib/jquery',
            xstatic.main.XStatic(xstatic.pkg.jquery,
                                 root_url=webroot).base_dir),
        ('horizon/lib/jquery',
            xstatic.main.XStatic(xstatic.pkg.jquery_migrate,
                                 root_url=webroot).base_dir),
        ('horizon/lib/jquery',
            xstatic.main.XStatic(xstatic.pkg.jquery_quicksearch,
                                 root_url=webroot).base_dir),
        ('horizon/lib/jquery',
            xstatic.main.XStatic(xstatic.pkg.jquery_tablesorter,
                                 root_url=webroot).base_dir),
        ('horizon/lib/jsencrypt',
            xstatic.main.XStatic(xstatic.pkg.jsencrypt,
                                 root_url=webroot).base_dir),
        ('horizon/lib/mdi',
         xstatic.main.XStatic(xstatic.pkg.mdi,
                              root_url=webroot).base_dir),
        ('horizon/lib/objectpath',
            xstatic.main.XStatic(xstatic.pkg.objectpath,
                                 root_url=webroot).base_dir),
        ('horizon/lib',
            xstatic.main.XStatic(xstatic.pkg.rickshaw,
                                 root_url=webroot).base_dir),
        ('horizon/lib/roboto_fontface',
         xstatic.main.XStatic(xstatic.pkg.roboto_fontface,
                              root_url=webroot).base_dir),
        ('horizon/lib',
            xstatic.main.XStatic(xstatic.pkg.spin,
                                 root_url=webroot).base_dir),
        ('horizon/lib',
         xstatic.main.XStatic(xstatic.pkg.termjs,
                              root_url=webroot).base_dir),
        ('horizon/lib/tv4',
            xstatic.main.XStatic(xstatic.pkg.tv4,
                                 root_url=webroot).base_dir),
    ]

    if xstatic.main.XStatic(xstatic.pkg.jquery_ui,
                            root_url=webroot).version.startswith('1.10.'):
        # The 1.10.x versions already contain the 'ui' directory.
        STATICFILES_DIRS.append(
            ('horizon/lib/jquery-ui',
             xstatic.main.XStatic(xstatic.pkg.jquery_ui,
                                  root_url=webroot).base_dir))
    else:
        # Newer versions dropped the directory, add it to keep the path the
        # same.
        STATICFILES_DIRS.append(
            ('horizon/lib/jquery-ui/ui',
             xstatic.main.XStatic(xstatic.pkg.jquery_ui,
                                  root_url=webroot).base_dir))

    return STATICFILES_DIRS


def find_static_files(
        HORIZON_CONFIG,
        AVAILABLE_THEMES,
        THEME_COLLECTION_DIR,
        ROOT_PATH):
    import horizon
    import openstack_dashboard
    os_dashboard_home_dir = openstack_dashboard.__path__[0]
    horizon_home_dir = horizon.__path__[0]

    # note the path must end in a '/' or the resultant file paths will have a
    # leading "/"
    file_discovery.populate_horizon_config(
        HORIZON_CONFIG,
        os.path.join(horizon_home_dir, 'static/')
    )

    # filter out non-angular javascript code and lib
    HORIZON_CONFIG['js_files'] = ([f for f in HORIZON_CONFIG['js_files']
                                   if not f.startswith('horizon/')])

    # note the path must end in a '/' or the resultant file paths will have a
    # leading "/"
    file_discovery.populate_horizon_config(
        HORIZON_CONFIG,
        os.path.join(os_dashboard_home_dir, 'static/'),
        sub_path='app/'
    )

    # Discover theme static resources, and in particular any
    # static HTML (client-side) that the theme overrides
    theme_static_files = {}
    theme_info = theme_settings.get_theme_static_dirs(
        AVAILABLE_THEMES,
        THEME_COLLECTION_DIR,
        ROOT_PATH)

    for url, path in theme_info:
        discovered_files = {}

        # discover static files provided by the theme
        file_discovery.populate_horizon_config(
            discovered_files,
            path
        )

        # Get the theme name from the theme url
        theme_name = url.split('/')[-1]

        # build a dictionary of this theme's static HTML templates.
        # For each overridden template, strip off the '/templates/' part of the
        # theme filename then use that name as the key, and the location in the
        # theme directory as the value. This allows the quick lookup of
        # theme path for any file overridden by a theme template
        template_overrides = {}
        for theme_file in discovered_files['external_templates']:
            # Example:
            #   external_templates_dict[
            #       'framework/widgets/help-panel/help-panel.html'
            #   ] = 'themes/material/templates/framework/widgets/\
            #        help-panel/help-panel.html'
            (templates_part, override_path) = theme_file.split('/templates/')
            template_overrides[override_path] = 'themes/' +\
                                                theme_name + theme_file

        discovered_files['template_overrides'] = template_overrides

        # Save all of the discovered file info for this theme in our
        # 'theme_files' object using the theme name as the key
        theme_static_files[theme_name] = discovered_files

    # Add the theme file info to the horizon config for use by template tags
    HORIZON_CONFIG['theme_static_files'] = theme_static_files
