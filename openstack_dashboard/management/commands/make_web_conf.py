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

import multiprocessing
import os
import re
import socket
import subprocess
import sys
import warnings

from django.conf import settings
from django.core.management import base
from django import template

# Suppress DeprecationWarnings which clutter the output to the point of
# rendering it unreadable.
warnings.simplefilter('ignore')

cmd_name = __name__.split('.')[-1]

CURDIR = os.path.realpath(os.path.dirname(__file__))
PROJECT_PATH = os.path.realpath(os.path.join(CURDIR, '../..'))
STATIC_PATH = os.path.realpath(os.path.join(PROJECT_PATH, '../static'))

# Known apache regular expression to retrieve it's version
APACHE_VERSION_REG = r'Apache/(?P<version>[\d.]*)'
# Known apache commands to retrieve it's version
APACHE2_VERSION_CMDS = (
    (('/usr/sbin/apache2ctl', '-V'), APACHE_VERSION_REG),
    (('/usr/sbin/apache2', '-v'), APACHE_VERSION_REG),
)

# Known apache log directory locations
APACHE_LOG_DIRS = (
    '/var/log/httpd',  # RHEL / Red Hat / CentOS / Fedora Linux
    '/var/log/apache2',  # Debian / Ubuntu Linux
)
# Default log directory
DEFAULT_LOG_DIR = '/var/log'


def _getattr(obj, name, default):
    """Like getattr but return `default` if None or False.

    By default, getattr(obj, name, default) returns default only if
    attr does not exist, here, we return `default` even if attr evaluates to
    None or False.
    """
    value = getattr(obj, name, default) or default
    return value


context = template.Context({
    'DJANGO_SETTINGS_MODULE': os.environ['DJANGO_SETTINGS_MODULE'],
    'HOSTNAME': socket.getfqdn(),
    'PROJECT_PATH': os.path.realpath(
        _getattr(settings, 'ROOT_PATH', PROJECT_PATH)),
    'STATIC_PATH': os.path.realpath(
        _getattr(settings, 'STATIC_ROOT', STATIC_PATH)),
    'SSLCERT': '/etc/pki/tls/certs/ca.crt',
    'SSLKEY': '/etc/pki/tls/private/ca.key',
    'CACERT': None,
    'PROCESSES': multiprocessing.cpu_count() + 1,
    'PYTHON_EXEC': sys.executable,
})

context['PROJECT_ROOT'] = os.path.dirname(context['PROJECT_PATH'])
context['PROJECT_DIR_NAME'] = os.path.basename(
    context['PROJECT_PATH'].split(context['PROJECT_ROOT'])[1])
context['PROJECT_NAME'] = context['PROJECT_DIR_NAME']

context['DEFAULT_WSGI_FILE'] = os.path.join(
    context['PROJECT_PATH'], 'wsgi.py')
context['WSGI_FILE'] = os.path.join(
    context['PROJECT_PATH'], 'horizon_wsgi.py')

VHOSTNAME = context['HOSTNAME'].split('.')
VHOSTNAME[0] = context['PROJECT_NAME']
context['VHOSTNAME'] = '.'.join(VHOSTNAME)

if len(VHOSTNAME) > 1:
    context['DOMAINNAME'] = '.'.join(VHOSTNAME[1:])
else:
    context['DOMAINNAME'] = 'openstack.org'
context['ADMIN'] = 'webmaster@%s' % context['DOMAINNAME']

context['ACTIVATE_THIS'] = None
virtualenv = os.environ.get('VIRTUAL_ENV')
if virtualenv:
    activate_this = os.path.join(
        virtualenv, 'bin/activate_this.py')
    if os.path.exists(activate_this):
        context['ACTIVATE_THIS'] = activate_this

# Try to detect apache's version
# We fallback on 2.4.
context['APACHE2_VERSION'] = 2.4
APACHE2_VERSION = None
for cmd in APACHE2_VERSION_CMDS:
    if os.path.exists(cmd[0][0]):
        try:
            reg = re.compile(cmd[1])
            output = subprocess.check_output(cmd[0], stderr=subprocess.STDOUT)
            if isinstance(output, bytes):
                output = output.decode()
            res = reg.search(output)
            if res:
                APACHE2_VERSION = res.group('version')
                break
        except subprocess.CalledProcessError:
            pass
if APACHE2_VERSION:
    ver_nums = APACHE2_VERSION.split('.')
    if len(ver_nums) >= 2:
        try:
            context['APACHE2_VERSION'] = float('.'.join(ver_nums[:2]))
        except ValueError:
            pass


def find_apache_log_dir():
    for log_dir in APACHE_LOG_DIRS:
        if os.path.exists(log_dir) and os.path.isdir(log_dir):
            return log_dir
    return DEFAULT_LOG_DIR


context['LOGDIR'] = find_apache_log_dir()


class Command(base.BaseCommand):

    args = ''
    help = """Create %(wsgi_file)s
or the contents of an apache %(p_name)s.conf file (on stdout).
The apache configuration is generated on stdout because the place of this
file is distribution dependent.

examples::

    manage.py %(cmd_name)s --wsgi  # creates %(wsgi_file)s
    manage.py %(cmd_name)s --apache  # creates an apache vhost conf file (on \
stdout).
    manage.py %(cmd_name)s --apache --ssl --mail=%(admin)s \
--project=%(p_name)s --hostname=%(hostname)s

To create an acpache configuration file, redirect the output towards the
location you desire, e.g.::

    manage.py %(cmd_name)s --apache > \
/etc/httpd/conf.d/openstack_dashboard.conf

    """ % {
           'cmd_name': cmd_name,
           'p_name': context['PROJECT_NAME'],
           'wsgi_file': context['WSGI_FILE'],
           'admin': context['ADMIN'],
           'hostname': context['VHOSTNAME'], }

    def add_arguments(self, parser):
        # TODO(ygbo): Add an --nginx option.
        parser.add_argument(
            "-a", "--apache",
            default=False, action="store_true", dest="apache",
            help="generate an apache vhost configuration"
        )
        parser.add_argument(
            "--cacert",
            dest="cacert",
            help=("Use with the --apache and --ssl option to define the path"
                  " to the SSLCACertificateFile"),
            metavar="CACERT"
        )
        parser.add_argument(
            "-f", "--force",
            default=False, action="store_true", dest="force",
            help="force overwriting of an existing %s file" %
            context['WSGI_FILE']
        )
        parser.add_argument(
            "-H", "--hostname",
            dest="hostname",
            help=("Use with the --apache option to define the server's"
                  " hostname (default : %s)") % context['VHOSTNAME'],
            metavar="HOSTNAME"
        )
        parser.add_argument(
            "--logdir",
            dest="logdir",
            help=("Use with the --apache option to define the path to "
                  "the apache log directory(default : %s)"
                  % context['LOGDIR']),
            metavar="CACERT"
        )
        parser.add_argument(
            "-m", "--mail",
            dest="mail",
            help=("Use with the --apache option to define the web site"
                  " administrator's email (default : %s)") %
                 context['ADMIN'],
            metavar="MAIL"
        )
        parser.add_argument(
            "-n", "--namedhost",
            default=False, action="store_true", dest="namedhost",
            help=("Use with the --apache option. The apache vhost "
                  "configuration will work only when accessed with "
                  "the proper hostname (see --hostname).")
        )
        parser.add_argument(
            "--processes",
            dest="processes",
            help=("Use with the --apache option to define the number of "
                  "apache processes (by default the number of cpus +1 which "
                  "is %s on this machine).") % context['PROCESSES'],
            metavar="PROCESSES"
        )
        parser.add_argument(
            "-p", "--project",
            dest="project",
            help=("Use with the --apache option to define the project "
                  "name (default : %s)") % context['PROJECT_NAME'],
            metavar="PROJECT"
        )
        parser.add_argument(
            "-s", "--ssl",
            default=False, action="store_true", dest="ssl",
            help=("Use with the --apache option. The apache vhost "
                  "configuration will use an SSL configuration")
        )
        parser.add_argument(
            "--sslcert",
            dest="sslcert",
            help=("Use with the --apache and --ssl option to define "
                  "the path to the SSLCertificateFile (default : %s)"
                  ) % context['SSLCERT'],
            metavar="SSLCERT"
        )
        parser.add_argument(
            "--sslkey",
            dest="sslkey",
            help=("Use with the --apache and --ssl option to define "
                  "the path to the SSLCertificateKeyFile "
                  "(default : %s)") % context['SSLKEY'],
            metavar="SSLKEY"
        )
        parser.add_argument(
            "--apache-version",
            dest="apache_version",
            type=float,
            help=("Use with the --apache option to define the apache "
                  "major (as a floating point number) version "
                  "(default : %s)."
                  % context['APACHE2_VERSION']),
            metavar="APACHE_VERSION"
        )
        parser.add_argument(
            "-w", "--wsgi",
            default=False, action="store_true", dest="wsgi",
            help="generate the horizon.wsgi file"
        )

    def handle(self, *args, **options):
        force = options.get('force')
        context['SSL'] = options.get('ssl')

        if options.get('mail'):
            context['ADMIN'] = options['mail']
        if options.get('cacert'):
            context['CACERT'] = options['cacert']
        if options.get('logdir'):
            context['LOGDIR'] = options['logdir'].rstrip('/')
        if options.get('processes'):
            context['PROCESSES'] = options['processes']
        if options.get('project'):
            context['PROJECT_NAME'] = options['project']
        if options.get('hostname'):
            context['VHOSTNAME'] = options['hostname']
        if options.get('sslcert'):
            context['SSLCERT'] = options['sslcert']
        if options.get('sslkey'):
            context['SSLKEY'] = options['sslkey']
        if options.get('apache_version'):
            context['APACHE2_VERSION'] = options['apache_version']

        if options.get('namedhost'):
            context['NAMEDHOST'] = context['VHOSTNAME']
        else:
            context['NAMEDHOST'] = '*'

        # Generate the WSGI.
        if options.get('wsgi'):
            with open(
                os.path.join(CURDIR, 'horizon.wsgi.template'), 'r'
            ) as fp:
                wsgi_template = template.Template(fp.read())
            if not os.path.exists(context['WSGI_FILE']) or force:
                with open(context['WSGI_FILE'], 'w') as fp:
                    fp.write(wsgi_template.render(context))
                print('Generated "%s"' % context['WSGI_FILE'])
            else:
                sys.exit('"%s" already exists, use --force to overwrite' %
                         context['WSGI_FILE'])

        # Generate the apache configuration.
        elif options.get('apache'):
            # first check if custom wsgi file exists, if not, use default:
            if not os.path.exists(context['WSGI_FILE']):
                context['WSGI_FILE'] = context['DEFAULT_WSGI_FILE']

            with open(
                os.path.join(CURDIR, 'apache_vhost.conf.template'), 'r'
            ) as fp:
                wsgi_template = template.Template(fp.read())
            sys.stdout.write(wsgi_template.render(context))
        else:
            self.print_help('manage.py', cmd_name)
