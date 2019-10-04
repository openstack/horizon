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
               default='http://localhost/dashboard/',
               help='Where the dashboard can be found'),
    cfg.StrOpt('help_url',
               default='https://docs.openstack.org/',
               help='Dashboard help page url'),
]

IdentityGroup = [
    cfg.StrOpt('username',
               default='demo',
               help='Username to use for non-admin API requests.'),
    cfg.StrOpt('password',
               default='secretadmin',
               help='API key to use when authenticating.',
               secret=True),
    cfg.StrOpt('domain',
               default=None,
               help='Domain name to use if required for login'),
    cfg.StrOpt('home_project',
               default='demo',
               help='Project to keep all objects belonging to a regular user.'
               ),
    cfg.StrOpt('admin_username',
               default='admin',
               help='Administrative Username to use for admin API requests.'),
    cfg.StrOpt('admin_password',
               default='secretadmin',
               help='API key to use when authenticating as admin.',
               secret=True),
    cfg.StrOpt('admin_home_project',
               default='admin',
               help='Project to keep all objects belonging to an admin user.'),
    cfg.StrOpt('default_keystone_role',
               default='member',
               help='Name of default role every user gets in his new project.'),
    cfg.StrOpt('default_keystone_admin_role',
               default='admin',
               help=('Name of the role that grants admin rights to a user in '
                     'his project')),
    cfg.IntOpt('unique_last_password_count',
               # The default value is chosen to match the value of
               # [security_compliance] unique_last_password_count in DevStack
               # as the first target of the integration tests is the gate.
               # Note that the default value of unique_last_password_count
               # in keystone may differ, so you might need
               # to change this parameter.
               default=2,
               help=('The number of passwords for a user that must be unique '
                     'before an old password can be used. '
                     'This should match the keystone configuration option '
                     '"[security_compliance] unique_last_password_count".')),
]

ImageGroup = [
    cfg.StrOpt('panel_type',
               default='angular',
               help='type/version of images panel'),
    cfg.StrOpt('http_image',
               default='http://download.cirros-cloud.net/0.3.1/'
                       'cirros-0.3.1-x86_64-uec.tar.gz',
               help='http accessible image'),
    cfg.ListOpt('images_list',
                default=['cirros-0.3.5-x86_64-disk'],
                help='default list of images')
]

NetworkGroup = [
    cfg.StrOpt('network_cidr',
               default='10.100.0.0/16',
               help='The cidr block to allocate tenant ipv4 subnets from'),
    cfg.StrOpt(
        'external_network',
        # Devstack default external network is 'public' but it
        # can be changed as per available external network.
        default='public',
        help='The external network for a router creation.'),
]

AvailableServiceGroup = [
    cfg.BoolOpt('neutron',
                default=True,
                help='Whether neutron is expected to be available'),
]

SeleniumGroup = [
    cfg.FloatOpt(
        'message_implicit_wait',
        default=0.1,
        help='Timeout in seconds to wait for message confirmation modal'),
    cfg.IntOpt(
        'implicit_wait',
        default=10,
        help=('Implicit timeout to wait until element become available, '
              'It is used for every find_element, find_elements call.')),
    cfg.IntOpt(
        'explicit_wait',
        default=90,
        help=('Explicit timeout is used for long lasting operations, '
              'Methods using explicit timeout are usually prefixed with '
              '"wait"')),
    cfg.IntOpt(
        'page_timeout',
        default=60,
        help='Timeout in seconds to wait for a page to become available'),
    cfg.StrOpt(
        'screenshots_directory',
        default='integration_tests_screenshots',
        help='Output directory for screenshots'),
    cfg.BoolOpt(
        'maximize_browser',
        default=True,
        help='Maximize the browser window at the start of each test or not'),
]

FlavorsGroup = [
    cfg.StrOpt('panel_type',
               default='legacy',
               help='type/version of flavors panel'),
]

ScenarioGroup = [
    cfg.StrOpt('ssh_user',
               default='cirros',
               help='ssh username for image file'),
]

InstancesGroup = [
    cfg.StrOpt('available_zone',
               default='nova',
               help='Availability zone to be selected for launch instances'),
    cfg.StrOpt('image_name',
               default='cirros-0.4.0-x86_64-disk (12.1 MB)',
               help='Boot Source to be selected for launch Instances'),
    cfg.StrOpt('flavor',
               default='m1.tiny',
               help='Flavor to be selected for launch instances'),
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
    cfg.BoolOpt(
        'is_plugin',
        default='False',
        help='Set to true if this is a plugin'),
    cfg.MultiStrOpt(
        'plugin_page_path',
        default='',
        help='Additional path to look for plugin page content'),
    cfg.MultiStrOpt(
        'plugin_page_structure',
        default='',
        help=('JSON string to define the page structure for the plugin')),
]


def _get_config_files():
    conf_dir = os.path.join(
        os.path.abspath(os.path.dirname(os.path.dirname(__file__))),
        'integration_tests')
    conf_file = os.environ.get('HORIZON_INTEGRATION_TESTS_CONFIG_FILE',
                               '%s/horizon.conf' % conf_dir)
    local_config = os.environ.get('HORIZON_INTEGRATION_TESTS_LOCAL_CONFIG',
                                  '%s/local-horizon.conf' % conf_dir)
    config_files = [conf_file, local_config]
    return [f for f in config_files if os.path.isfile(f)]


def get_config():
    cfg.CONF([], project='horizon', default_config_files=_get_config_files())

    cfg.CONF.register_opts(DashboardGroup, group="dashboard")
    cfg.CONF.register_opts(IdentityGroup, group="identity")
    cfg.CONF.register_opts(NetworkGroup, group="network")
    cfg.CONF.register_opts(AvailableServiceGroup, group="service_available")
    cfg.CONF.register_opts(SeleniumGroup, group="selenium")
    cfg.CONF.register_opts(FlavorsGroup, group="flavors")
    cfg.CONF.register_opts(ImageGroup, group="image")
    cfg.CONF.register_opts(ScenarioGroup, group="scenario")
    cfg.CONF.register_opts(InstancesGroup, group="launch_instances")
    cfg.CONF.register_opts(PluginGroup, group="plugin")
    cfg.CONF.register_opts(VolumeGroup, group="volume")

    return cfg.CONF


def list_opts():
    return [
        ("dashboard", DashboardGroup),
        ("selenium", SeleniumGroup),
        ("flavors", FlavorsGroup),
        ("image", ImageGroup),
        ("identity", IdentityGroup),
        ("network", NetworkGroup),
        ("service_available", AvailableServiceGroup),
        ("scenario", ScenarioGroup),
        ("launch_instances", InstancesGroup),
        ("plugin", PluginGroup),
        ("volume", VolumeGroup),
    ]
