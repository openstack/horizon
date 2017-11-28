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
This module contains utility functions for loading Horizon's
configuration from .ini files using the oslo.config library.
"""

import six

from oslo_config import cfg

# XXX import the actual config groups here
# from openstack_dashboard.config import config_compress


def load_config(files=None, root_path=None, local_path=None):
    """Load the configuration from specified files."""

    config = cfg.ConfigOpts()
    config.register_opts([
        cfg.Opt('root_path', default=root_path),
        cfg.Opt('local_path', default=local_path),
    ])
    # XXX register actual config groups here
    # theme_group = config_theme.register_config(config)
    if files is not None:
        config(args=[], default_config_files=files)
    return config


def apply_config(config, target):
    """Apply the configuration on the specified settings module."""
    # TODO(rdopiera) fill with actual config groups
    # apply_config_group(config.email, target, 'email')


def apply_config_group(config_group, target, prefix=None):
    for key, value in six.iteritems(config_group):
        name = key.upper()
        if prefix:
            name = '_'.join([prefix.upper(), name])
        target[name] = value


def list_options():
    # This is a really nasty hack to make the translatable strings
    # work without having to initialize Django and read all the settings.
    from django.apps import registry
    from django.conf import settings

    settings.configure()
    registry.apps.check_apps_ready = lambda: True

    config = load_config()
    return [
        (name, [d['opt'] for d in group._opts.values()])
        for (name, group) in config._groups.items()
    ]
