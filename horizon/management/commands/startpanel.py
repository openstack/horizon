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

import glob
from importlib import import_module
import os

from django.core.management.base import CommandError
from django.core.management.templates import TemplateCommand

import horizon


class Command(TemplateCommand):
    template = os.path.join(horizon.__path__[0], "conf", "panel_template")
    help = ("Creates a Django app directory structure for a new panel "
            "with the given name in the current directory or optionally in "
            "the given directory.")

    def add_arguments(self, parser):
        add = parser.add_argument
        add('panel_name', help='Panel name')
        add('--template', help='The path or URL to load the template from.')
        add('--extension', '-e', dest='extensions', action='append',
            default=["py", "tmpl", "html"],
            help='The file extension(s) to render (default: "py"). Separate '
            'multiple extensions with commas, or use -e multiple times.')
        add('--name', '-n', dest='files', action='append', default=[],
            help='The file name(s) to render. Separate multiple extensions '
            'with commas, or use -n multiple times.')
        add('--dashboard', '-d', dest='dashboard', action='store',
            default=None,
            help='The dotted python path to the dashboard which this panel '
            'will be registered with.')
        add('--target', dest='target', action='store', default=None,
            help='The directory in which the panel should be created. '
            'Defaults to the current directory. The value "auto" may also be '
            'used to automatically create the panel inside the specified '
            'dashboard module.')

    def handle(self, panel_name=None, **options):
        if panel_name is None:
            raise CommandError("You must provide a panel name.")

        if options.get('dashboard'):
            dashboard_path = options.get('dashboard')
            dashboard_mod_path = ".".join([dashboard_path, "dashboard"])

        # Check the dashboard.py file in the dashboard app can be imported.
        # Add the dashboard information to our options to pass along if all
        # goes well.
            try:
                dashboard_mod = import_module(dashboard_mod_path)
                options["dash_path"] = dashboard_path
                options["dash_name"] = dashboard_path.split(".")[-1]
            except ImportError:
                raise CommandError("A dashboard.py module could not be "
                                   "imported from the dashboard at %r."
                                   % options.get("dashboard"))

        target = options.pop("target", None)
        if target == "auto":
            target = os.path.join(os.path.dirname(dashboard_mod.__file__),
                                  panel_name)
            if not os.path.exists(target):
                try:
                    os.mkdir(target)
                except OSError as exc:
                    raise CommandError("Unable to create panel directory: %s"
                                       % exc)

        # Use our default template if one isn't specified.
        if not options.get("template", None):
            options["template"] = self.template

        # Check that the app_name cannot be imported.
        try:
            import_module(panel_name)
        except ImportError:
            pass
        else:
            raise CommandError("%r conflicts with the name of an existing "
                               "Python module and cannot be used as an app "
                               "name. Please try another name." % panel_name)

        super().handle('panel', panel_name, target, **options)

        if not target:
            target = os.path.join(os.curdir, panel_name)

        # Rename our python template files.
        file_names = glob.glob(os.path.join(target, "*.py.tmpl"))
        for filename in file_names:
            os.rename(filename, filename[:-5])
