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

from __future__ import print_function

import difflib
import imp
import optparse
import os
import shlex
import subprocess
import sys
import time
import warnings

from django.core.management.templates import BaseCommand  # noqa

# Suppress DeprecationWarnings which clutter the output to the point of
# rendering it unreadable.
warnings.simplefilter('ignore')


def get_module_path(module_name):
    """Gets the module path without importing anything.

    Avoids conflicts with package dependencies.
    (taken from http://github.com/sitkatech/pypatch)
    """
    path = sys.path
    for name in module_name.split('.'):
        file_pointer, path, desc = imp.find_module(name, path)
        path = [path, ]
        if file_pointer is not None:
            file_pointer.close()

    return path[0]


class DirContext(object):
    """Change directory in a context manager.

    This allows changing directory and to always fall back to the previous
    directory whatever happens during execution.

    Usage::

        with DirContext('/home/foo') as dircontext:
            # Some code happening in '/home/foo'
        # We are back to the previous directory.

    """

    def __init__(self, dirname):
        self.prevdir = os.path.abspath(os.curdir)
        os.chdir(dirname)
        self.curdir = os.path.abspath(os.curdir)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        os.chdir(self.prevdir)

    def __str__(self):
        return self.curdir


class Command(BaseCommand):
    option_list = BaseCommand.option_list + (
        optparse.make_option(
            '--gendiff',
            action='store_true',
            dest='gendiff',
            default=False,
            help=('Generate a diff file between local_settings.py and '
                  'local_settings.py.example'),
        ),
        optparse.make_option(
            '-f', '--force',
            action='store_true',
            dest='force',
            default=False,
            help=('Force destination rewriting without warning if the '
                  'destination file already exists.'),
        ),
    )

    help = ("Creates a local_settings.py file from the "
            "local_settings.py.example template.")

    time_fmt = '%Y-%m-%d %H:%M:%S %Z'
    file_time_fmt = '%Y%m%d%H%M%S%Z'

    local_settings_example = 'local_settings.py.example'
    local_settings_file = 'local_settings.py'
    local_settings_diff = 'local_settings.diff'
    local_settings_reject_pattern = 'local_settings.py_%s.rej'

    def __init__(self, *args, **kwargs):
        super(Command, self).__init__(*args, **kwargs)

        settings_file = os.path.abspath(
            get_module_path(os.environ['DJANGO_SETTINGS_MODULE'])
        )

        self.local_settings_dir = os.path.abspath(
            os.path.join(
                os.path.realpath(os.path.dirname(settings_file)),
                'local'
            )
        )

    def gendiff(self, force=False):
        """Generate a diff between self.local_settings and the example file.

        """

        with DirContext(self.local_settings_dir) as dircontext:
            if not os.path.exists(self.local_settings_diff) or force:
                with open(self.local_settings_example, 'r') as fp:
                    example_lines = fp.readlines()
                with open(self.local_settings_file, 'r') as fp:
                    local_settings_lines = fp.readlines()
                local_settings_example_mtime = time.strftime(
                    self.time_fmt,
                    time.localtime(
                        os.stat(self.local_settings_example).st_mtime)
                )

                local_settings_mtime = time.strftime(
                    self.time_fmt,
                    time.localtime(os.stat(self.local_settings_file).st_mtime)
                )

                print('generating "%s"...' % os.path.join(
                    dircontext.curdir,
                    self.local_settings_diff)
                )
                with open(self.local_settings_diff, 'w') as fp:
                    for line in difflib.unified_diff(
                        example_lines, local_settings_lines,
                        fromfile=self.local_settings_example,
                        tofile=self.local_settings_file,
                        fromfiledate=local_settings_example_mtime,
                        tofiledate=local_settings_mtime
                    ):
                        fp.write(line)
                print('\tDONE.')
                sys.exit(0)
            else:
                sys.exit(
                    '"%s" already exists.' %
                    os.path.join(dircontext.curdir,
                                 self.local_settings_diff)
                )

    def patch(self, force=False):
        """Patch local_settings.py.example with local_settings.diff.

        The patch application generates the local_settings.py file (the
        local_settings.py.example remains unchanged).

        http://github.com/sitkatech/pypatch fails if the
        local_settings.py.example file is not 100% identical to the one used to
        generate the first diff so we use the patch command instead.

        """

        with DirContext(self.local_settings_dir) as dircontext:
            if os.path.exists(self.local_settings_diff):
                if not os.path.exists(self.local_settings_file) or force:
                    local_settings_reject = \
                        self.local_settings_reject_pattern % (
                            time.strftime(self.file_time_fmt, time.localtime())
                        )
                    patch_cmd = shlex.split(
                        'patch %s %s -o %s -r %s' % (
                            self.local_settings_example,
                            self.local_settings_diff,
                            self.local_settings_file,
                            local_settings_reject
                        )
                    )
                    try:
                        subprocess.check_call(patch_cmd)
                    except subprocess.CalledProcessError:
                        if os.path.exists(local_settings_reject):
                            sys.exit(
                                'Some conflict(s) occurred. Please check "%s" '
                                'to find unapplied parts of the diff.\n'
                                'Once conflicts are solved, it is safer to '
                                'regenerate a newer diff with the "--gendiff" '
                                'option.' %
                                os.path.join(
                                    dircontext.curdir,
                                    local_settings_reject)
                            )
                        else:
                            sys.exit('An unhandled error occurred.')
                    print('Generation of "%s" successful.' % os.path.join(
                        dircontext.curdir,
                        self.local_settings_file)
                    )
                    sys.exit(0)
                else:
                    sys.exit(
                        '"%s" already exists.' %
                        os.path.join(dircontext.curdir,
                                     self.local_settings_file)
                    )
            else:
                sys.exit('No diff file found, please generate one with the '
                         '"--gendiff" option.')

    def handle(self, *args, **options):
        force = options.get('force')
        if options.get('gendiff'):
            self.gendiff(force)
        else:
            self.patch(force)
