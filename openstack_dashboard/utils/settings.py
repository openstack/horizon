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
import os
import pkgutil

from django.utils import importlib
import six

from horizon.utils import file_discovery as fd


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
        for key, submodule in six.iteritems(import_submodules(module)):
            if hasattr(submodule, 'DASHBOARD'):
                dashboard = submodule.DASHBOARD
                config[dashboard].update(submodule.__dict__)
            elif (hasattr(submodule, 'PANEL')
                  or hasattr(submodule, 'PANEL_GROUP')
                  or hasattr(submodule, 'FEATURE')):
                config[submodule.__name__] = submodule.__dict__
            else:
                logging.warning("Skipping %s because it doesn't have DASHBOARD"
                                ", PANEL, PANEL_GROUP, or FEATURE defined.",
                                submodule.__name__)
    return sorted(six.iteritems(config),
                  key=lambda c: c[1]['__name__'].rsplit('.', 1))


def update_dashboards(modules, horizon_config, installed_apps):
    """Imports dashboard and panel configuration from modules and applies it.

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

    Panel specific configurations are stored in horizon_config. Dashboards
    from both plugin-based and openstack_dashboard must be registered before
    the panel configuration can be applied. Making changes to the panel is
    deferred until the horizon autodiscover is completed, configurations are
    applied in alphabetical order of files where it was imported.
    """
    config_dashboards = horizon_config.get('dashboards', [])
    if config_dashboards or horizon_config.get('default_dashboard'):
        logging.warning(
            '"dashboards" and "default_dashboard" in (local_)settings is '
            'DEPRECATED now and may be unsupported in some future release. '
            'The preferred way to specify the order of dashboards and the '
            'default dashboard is the pluggable dashboard mechanism (in %s).',
            ', '.join([os.path.abspath(module.__path__[0])
                       for module in modules])
        )

    enabled_dashboards = []
    disabled_dashboards = []
    exceptions = horizon_config.get('exceptions', {})
    apps = []
    angular_modules = []
    js_files = []
    js_spec_files = []
    scss_files = []
    panel_customization = []
    update_horizon_config = {}
    for key, config in import_dashboard_config(modules):
        if config.get('DISABLED', False):
            if config.get('DASHBOARD'):
                disabled_dashboards.append(config.get('DASHBOARD'))
            continue

        _apps = config.get('ADD_INSTALLED_APPS', [])
        apps.extend(_apps)

        if config.get('AUTO_DISCOVER_STATIC_FILES', False):
            for _app in _apps:
                module = importlib.import_module(_app)
                base_path = os.path.join(module.__path__[0], 'static/')
                fd.populate_horizon_config(horizon_config, base_path)

        add_exceptions = six.iteritems(config.get('ADD_EXCEPTIONS', {}))
        for category, exc_list in add_exceptions:
            exceptions[category] = tuple(set(exceptions.get(category, ())
                                             + exc_list))

        angular_modules.extend(config.get('ADD_ANGULAR_MODULES', []))
        # avoid pulling in dashboard javascript dependencies multiple times
        existing = set(js_files)
        js_files.extend([f for f in config.get('ADD_JS_FILES', [])
                         if f not in existing])
        js_spec_files.extend(config.get('ADD_JS_SPEC_FILES', []))
        scss_files.extend(config.get('ADD_SCSS_FILES', []))
        update_horizon_config.update(
            config.get('UPDATE_HORIZON_CONFIG', {}))
        if config.get('DASHBOARD'):
            dashboard = key
            enabled_dashboards.append(dashboard)
            if config.get('DEFAULT', False):
                horizon_config['default_dashboard'] = dashboard
        elif config.get('PANEL') or config.get('PANEL_GROUP'):
            config.pop("__builtins__", None)
            panel_customization.append(config)
    # Preserve the dashboard order specified in settings
    dashboards = ([d for d in config_dashboards
                   if d not in disabled_dashboards] +
                  [d for d in enabled_dashboards
                   if d not in config_dashboards])

    horizon_config['panel_customization'] = panel_customization
    horizon_config['dashboards'] = tuple(dashboards)
    horizon_config.setdefault('exceptions', {}).update(exceptions)
    horizon_config.update(update_horizon_config)
    horizon_config.setdefault('angular_modules', []).extend(angular_modules)
    horizon_config.setdefault('js_files', []).extend(js_files)
    horizon_config.setdefault('js_spec_files', []).extend(js_spec_files)
    horizon_config.setdefault('scss_files', []).extend(scss_files)

    # apps contains reference to applications declared in the enabled folder
    # basically a list of applications that are internal and external plugins
    # installed_apps contains reference to applications declared in settings
    # such as django.contribe.*, django_pyscss, compressor, horizon, etc...
    # for translation, we are only interested in the list of external plugins
    # so we save the reference to it before we append to installed_apps
    horizon_config.setdefault('plugins', []).extend(apps)
    installed_apps[0:0] = apps
