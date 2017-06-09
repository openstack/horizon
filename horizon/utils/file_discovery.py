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

import logging

from os import path
from os import walk

LOG = logging.getLogger(__name__)

MODULE_EXT = '.module.js'
MOCK_EXT = '.mock.js'
SPEC_EXT = '.spec.js'


def discover_files(base_path, sub_path='', ext='', trim_base_path=False):
    """Discovers all files with certain extension in given paths."""
    file_list = []
    for root, dirs, files in walk(path.join(base_path, sub_path)):
        if trim_base_path:
            root = path.relpath(root, base_path)
        file_list.extend([path.join(root, file_name)
                          for file_name in files
                          if file_name.endswith(ext)])
    return sorted(file_list)


def sort_js_files(js_files):
    """Sorts JavaScript files in `js_files`.

    It sorts JavaScript files in a given `js_files`
    into source files, mock files and spec files based on file extension.

    Output:

    * sources: source files for production.  The order of source files
      is significant and should be listed in the below order:

      - First, all the that defines the other application's angular module.
        Those files have extension of `.module.js`.  The order among them is
        not significant.

      - Followed by all other source code files.  The order among them
        is not significant.

    * mocks: mock files provide mock data/services for tests.  They have
      extension of `.mock.js`. The order among them is not significant.

    * specs: spec files for testing.  They have extension of `.spec.js`.
      The order among them is not significant.

    """
    modules = [f for f in js_files if f.endswith(MODULE_EXT)]
    mocks = [f for f in js_files if f.endswith(MOCK_EXT)]
    specs = [f for f in js_files if f.endswith(SPEC_EXT)]

    other_sources = [f for f in js_files if
                     not f.endswith(MODULE_EXT)
                     and not f.endswith(MOCK_EXT)
                     and not f.endswith(SPEC_EXT)]

    sources = modules + other_sources
    return sources, mocks, specs


def discover_static_files(base_path, sub_path=''):
    """Discovers static files in given paths.

    It returns JavaScript sources, mocks, specs and HTML templates,
    all grouped in lists.
    """
    js_files = discover_files(base_path, sub_path=sub_path,
                              ext='.js', trim_base_path=True)
    sources, mocks, specs = sort_js_files(js_files)
    html_files = discover_files(base_path, sub_path=sub_path,
                                ext='.html', trim_base_path=True)

    p = path.join(base_path, sub_path)
    _log(sources, 'JavaScript source', p)
    _log(mocks, 'JavaScript mock', p)
    _log(specs, 'JavaScript spec', p)
    _log(html_files, 'HTML template', p)

    return sources, mocks, specs, html_files


def populate_horizon_config(horizon_config, base_path,
                            sub_path='', prepend=False):
    sources, mocks, specs, template = discover_static_files(
        base_path, sub_path=sub_path)
    if prepend:
        horizon_config.setdefault('js_files', [])[:0] = sources
        horizon_config.setdefault('js_spec_files', [])[:0] = mocks + specs
        horizon_config.setdefault('external_templates', [])[:0] = template
    else:
        horizon_config.setdefault('js_files', []).extend(sources)
        horizon_config.setdefault('js_spec_files', []).extend(mocks + specs)
        horizon_config.setdefault('external_templates', []).extend(template)


def _log(file_list, list_name, in_path):
    """Logs result at debug level"""
    file_names = '\n'.join(file_list)
    LOG.debug("\nDiscovered %(size)d %(name)s file(s) in %(path)s:\n"
              "%(files)s\n",
              {'size': len(file_list), 'name': list_name, 'path': in_path,
               'files': file_names})
