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
    cfg.StrOpt('home_project',
               default='demo',
               help="Project to keep all objects belonging to a regular user."
               ),
    cfg.StrOpt('admin_username',
               default='admin',
               help="Administrative Username to use for admin API "
               "requests."),
    cfg.StrOpt('admin_password',
               default='secretadmin',
               help="API key to use when authenticating as admin.",
               secret=True),
    cfg.StrOpt('admin_home_project',
               default='admin',
               help="Project to keep all objects belonging to an admin user."),
]

ImageGroup = [
    cfg.StrOpt('http_image',
               default='http://download.cirros-cloud.net/0.3.1/'
                       'cirros-0.3.1-x86_64-uec.tar.gz',
               help='http accessible image'),
    cfg.ListOpt('images_list',
                default=['cirros-0.3.4-x86_64-uec',
                         'cirros-0.3.4-x86_64-uec-kernel',
                         'cirros-0.3.4-x86_64-uec-ramdisk'],
                help='default list of images')
]

NetworkGroup = [
    cfg.StrOpt('network_cidr',
               default='10.100.0.0/16',
               help='The cidr block to allocate tenant ipv4 subnets from'),
]

AvailableServiceGroup = [
    cfg.BoolOpt('neutron',
                default=True),
    cfg.BoolOpt('heat',
                default=True),
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
    cfg.BoolOpt('maximize_browser',
                default=True,
                help="Is the browser size maximized for each test?"),
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
    cfg.StrOpt('flavor',
               default='m1.tiny',
               help="Flavor to be selected for launch Instances"),
]

VolumeGroup = [
    cfg.StrOpt('volume_type',
               default='lvmdriver-1',
               help='Default volume type'),
    cfg.StrOpt('volume_size',
               default='1',
               help='Default volume size ')
]

PluginGroup = [
    cfg.BoolOpt('is_plugin',
                default='False',
                help="Set to true if this is a plugin"),
    cfg.MultiStrOpt('plugin_page_path',
                    default='',
                    help='Additional path to look for plugin page content'),
    cfg.MultiStrOpt('plugin_page_structure',
                    default='')
]


def _get_config_files():
    conf_dir = os.path.join(
        os.path.abspath(os.path.dirname(os.path.dirname(__file__))),
        'integration_tests')
    conf_file = os.environ.get('HORIZON_INTEGRATION_TESTS_CONFIG_FILE',
                               "%s/horizon.conf" % conf_dir)
    config_files = [conf_file]
    local_config = os.environ.get('HORIZON_INTEGRATION_TESTS_LOCAL_CONFIG',
                                  "%s/local-horizon.conf" % conf_dir)
    if os.path.isfile(local_config):
        config_files.append(local_config)
    return config_files


def get_config():
    cfg.CONF([], project='horizon', default_config_files=_get_config_files())

    cfg.CONF.register_opts(DashboardGroup, group="dashboard")
    cfg.CONF.register_opts(IdentityGroup, group="identity")
    cfg.CONF.register_opts(NetworkGroup, group="network")
    cfg.CONF.register_opts(AvailableServiceGroup, group="service_available")
    cfg.CONF.register_opts(SeleniumGroup, group="selenium")
    cfg.CONF.register_opts(ImageGroup, group="image")
    cfg.CONF.register_opts(ScenarioGroup, group="scenario")
    cfg.CONF.register_opts(InstancesGroup, group="launch_instances")
    cfg.CONF.register_opts(PluginGroup, group="plugin")
    cfg.CONF.register_opts(VolumeGroup, group="volume")

    return cfg.CONF
