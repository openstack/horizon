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
from optparse import make_option  # noqa
import os

from django.core.management.base import CommandError  # noqa
from django.core.management.templates import TemplateCommand  # noqa
from django.utils.importlib import import_module  # noqa

import horizon


class Command(TemplateCommand):
    template = os.path.join(horizon.__path__[0], "conf", "dash_template")
    option_list = TemplateCommand.option_list + (
        make_option('--target',
                    dest='target',
                    action='store',
                    default=None,
                    help='The directory in which the panel '
                         'should be created. Defaults to the '
                         'current directory. The value "auto" '
                         'may also be used to automatically '
                         'create the panel inside the specified '
                         'dashboard module.'),)
    help = ("Creates a Django app directory structure for a new dashboard "
            "with the given name in the current directory or optionally in "
            "the given directory.")

    def handle(self, dash_name=None, **options):
        if dash_name is None:
            raise CommandError("You must provide a dashboard name.")

        # Use our default template if one isn't specified.
        if not options.get("template", None):
            options["template"] = self.template

        # We have html templates as well, so make sure those are included.
        options["extensions"].extend(["tmpl", "html", "js", "css"])

        # Check that the app_name cannot be imported.
        try:
            import_module(dash_name)
        except ImportError:
            pass
        else:
            raise CommandError("%r conflicts with the name of an existing "
                               "Python module and cannot be used as an app "
                               "name. Please try another name." % dash_name)

        super(Command, self).handle('dash', dash_name, **options)

        target = options.pop("target", None)
        if not target:
            target = os.path.join(os.curdir, dash_name)

        # Rename our python template files.
        file_names = glob.glob(os.path.join(target, "*.py.tmpl"))
        for filename in file_names:
            os.rename(filename, filename[:-5])
