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

import os

from oslo_config import cfg


DashboardGroup = [
    cfg.StrOpt('dashboard_url',
               default='http://localhost/',
               help="Where the dashboard can be found"),
    cfg.StrOpt('login_url',
               default='http://localhost/auth/login/',
               help="Login page for the dashboard"),
    cfg.StrOpt('help_url',
               default='http://docs.openstack.org/',
               help="Dashboard help page url"),
]

IdentityGroup = [
    cfg.StrOpt('username',
               default='demo',
               help="Username to use for non-admin API requests."),
    cfg.StrOpt('password',
               default='secretadmin',
               help="API key to use when authenticating.",
               secret=True),
    cfg.StrOpt('admin_username',
               default='admin',
               help="Administrative Username to use for admin API "
               "requests."),
    cfg.StrOpt('admin_password',
               default='secretadmin',
               help="API key to use when authenticating as admin.",
               secret=True),
]

ImageGroup = [
    cfg.StrOpt('http_image',
               default='http://download.cirros-cloud.net/0.3.1/'
                       'cirros-0.3.1-x86_64-uec.tar.gz',
               help='http accessible image'),
]

AvailableServiceGroup = [
    cfg.BoolOpt('sahara',
                default=True,
                help='Whether is Sahara expected to be available')
]

SeleniumGroup = [
    cfg.IntOpt('implicit_wait',
               default=10,
               help="Implicit wait timeout in seconds"),
    cfg.IntOpt('explicit_wait',
               default=300,
               help="Explicit wait timeout in seconds"),
    cfg.IntOpt('page_timeout',
               default=30,
               help="Page load timeout in seconds"),
    cfg.StrOpt('screenshots_directory',
               default="integration_tests_screenshots",
               help="Output screenshot directory"),
]

ScenarioGroup = [
    cfg.StrOpt('ssh_user',
               default='cirros',
               help='ssh username for image file'),
]

InstancesGroup = [
    cfg.StrOpt('available_zone',
               default='nova',
               help="Zone to be selected for launch Instances"),
    cfg.StrOpt('image_name',
               default='cirros-0.3.4-x86_64-uec (24.0 MB)',
               help="Boot Source to be selected for launch Instances"),
]


def _get_config_files():
    conf_dir = os.path.join(
        os.path.abspath(os.path.dirname(os.path.dirname(__file__))),
        'integration_tests')
    conf_file = os.environ.get('HORIZON_INTEGRATION_TESTS_CONFIG_FILE',
                               "%s/horizon.conf" % conf_dir)
    return [conf_file]


def get_config():
    cfg.CONF([], project='horizon', default_config_files=_get_config_files())

    cfg.CONF.register_opts(DashboardGroup, group="dashboard")
    cfg.CONF.register_opts(IdentityGroup, group="identity")
    cfg.CONF.register_opts(AvailableServiceGroup, group="service_available")
    cfg.CONF.register_opts(SeleniumGroup, group="selenium")
    cfg.CONF.register_opts(ImageGroup, group="image")
    cfg.CONF.register_opts(ScenarioGroup, group="scenario")
    cfg.CONF.register_opts(InstancesGroup, group="launch_instances")

    return cfg.CONF
