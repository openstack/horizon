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

import os.path

from compressor.filters.base import FilterBase
from django.contrib.staticfiles.finders import get_finders

import sass


def importer(path, prev):
    if path.startswith('/'):
        # An absolute path was used, don't try relative paths.
        candidates = [path[1:]]
    elif prev == 'stdin':
        # The parent is STDIN, so only try absolute paths.
        candidates = [path]
    else:
        # Try both relative and absolute paths, prefer relative.
        candidates = [
            os.path.normpath(os.path.join(os.path.dirname(prev), path)),
            path,
        ]
    # Try adding _ in front of the file for partials.
    for candidate in candidates[:]:
        if '/' in candidate:
            candidates.insert(0, '/_'.join(candidate.rsplit('/', 1)))
        else:
            candidates.insert(0, '_' + candidate)
    # Try adding extensions.
    for candidate in candidates[:]:
        for ext in ['.scss', '.sass', '.css']:
            candidates.append(candidate + ext)
    for finder in get_finders():
        # We can't use finder.find() because we need the prefixes.
        for storage_filename, storage in finder.list([]):
            prefix = getattr(storage, "prefix", "")
            filename = os.path.join(prefix, storage_filename)
            if filename in candidates:
                with storage.open(storage_filename) as f:
                    data = f.read()
                return [(filename, data)]


class ScssFilter(FilterBase):
    def __init__(self, content, attrs=None, filter_type=None, charset=None,
                 filename=None):
        super().__init__(
            content=content, filter_type=filter_type, filename=filename)

    def input(self, **kwargs):
        args = {
            'importers': [(0, importer)],
            'output_style': 'compressed',
        }
        if self.filename:
            args['filename'] = self.filename
        else:
            args['string'] = self.content
        return sass.compile(**args)
