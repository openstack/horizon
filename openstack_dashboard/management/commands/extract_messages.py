# Copyright 2016 Cisco Systems, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# pylint: disable=import-error
from distutils.dist import Distribution
import os
from subprocess import call

from django.core.management.base import BaseCommand

DOMAINS = ['django', 'djangojs']
MODULES = ['openstack_dashboard', 'horizon']


class Command(BaseCommand):
    help = ('Extract strings that have been marked for translation into .POT '
            'files.')

    def add_arguments(self, parser):
        parser.add_argument('-m', '--module', type=str, nargs='+',
                            default=MODULES,
                            help=("The target python module(s) to extract "
                                  "strings from. "
                                  "Default: %s" % MODULES))
        parser.add_argument('-d', '--domain', choices=DOMAINS,
                            nargs='+', default=DOMAINS,
                            metavar='DOMAIN',
                            help=("Domain(s) of the .pot file. "
                                  "Default: %s" % DOMAINS))
        parser.add_argument('--check-only', action='store_true',
                            help=("Checks that extraction works correctly, "
                                  "then deletes the .pot file to avoid "
                                  "polluting the source code"))

    def handle(self, *args, **options):
        cmd = ('python setup.py {quiet} extract_messages '
               '-F babel-{domain}.cfg '
               '--input-dirs {module} '
               '-o {potfile}')
        distribution = Distribution()
        distribution.parse_config_files(distribution.find_config_files())

        quiet = '-q' if int(options['verbosity']) == 0 else ''
        if options['check_only']:
            cmd += " ; rm {potfile}"

        for module in options['module']:
            for domain in options['domain']:
                potfile = '{module}/locale/{domain}.pot'.format(module=module,
                                                                domain=domain)
                if not os.path.exists(potfile):
                    with open(potfile, 'wb') as f:
                        f.write(b'')

                call(cmd.format(module=module, domain=domain, potfile=potfile,
                                quiet=quiet), shell=True)
