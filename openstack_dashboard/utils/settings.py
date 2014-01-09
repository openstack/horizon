# vim: tabstop=4 shiftwidth=4 softtabstop=4

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

import collections
import logging
import pkgutil

from django.utils import importlib


def import_submodules(module):
    """Import all submodules and make them available in a dict."""
    submodules = {}
    for loader, name, ispkg in pkgutil.iter_modules(module.__path__,
                                                    module.__name__ + '.'):
        try:
            submodule = importlib.import_module(name)
        except ImportError as e:
            # FIXME: Make the errors non-fatal (do we want that?).
            logging.warning("Error importing %s" % name)
            logging.exception(e)
        else:
            parent, child = name.rsplit('.', 1)
            submodules[child] = submodule
    return submodules


def import_dashboard_config(modules):
    """Imports configuration from all the modules and merges it."""
    config = collections.defaultdict(dict)
    for module in modules:
        for key, submodule in import_submodules(module).iteritems():
            try:
                dashboard = submodule.DASHBOARD
            except AttributeError:
                logging.warning("Skipping %s because it doesn't "
                                "have DASHBOARD defined." % submodule.__name__)
            else:
                config[dashboard].update(submodule.__dict__)
    return sorted(config.iteritems(),
                  key=lambda c: c[1]['__name__'].rsplit('.', 1))


def update_dashboards(modules, horizon_config, installed_apps):
    """Imports dashboard configuration from modules and applies it.

    The submodules from specified modules are imported, and the configuration
    for the specific dashboards is merged, with the later modules overriding
    settings from the former. Then the configuration is applied to
    horizon_config and installed_apps, in alphabetical order of files from
    which the configurations were imported.

    For example, given this setup:

        | foo/__init__.py
        | foo/_10_baz.py
        | foo/_20_qux.py

        | bar/__init__.py
        | bar/_30_baz_.py

    and being called with ``modules=[foo, bar]``, we will first have the
    configuration from ``_10_baz`` and ``_30_baz`` merged, then the
    configurations will be applied in order ``qux``, ``baz`` (``baz`` is
    second, because the most recent file which contributed to it, ``_30_baz``,
    comes after ``_20_qux``).
    """
    dashboards = []
    exceptions = {}
    apps = []
    for dashboard, config in import_dashboard_config(modules):
        if config.get('DISABLED', False):
            continue
        dashboards.append(dashboard)
        exceptions.update(config.get('ADD_EXCEPTIONS', {}))
        apps.extend(config.get('ADD_INSTALLED_APPS', []))
        if config.get('DEFAULT', False):
            horizon_config['default_dashboard'] = dashboard
    horizon_config['dashboards'] = tuple(dashboards)
    horizon_config['exceptions'].update(exceptions)
    installed_apps.extend(apps)
