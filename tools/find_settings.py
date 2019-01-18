#!/usr/bin/env python3
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
A script that scans the source code looking for any use of Django
settings, and compiles a list of possible settings options.
"""

import os
import re


SETTINGS_RE = re.compile(r"""
# Straight use of a setting.
    \bsettings[.](\w+)
    |
# Using getattr with a default value.
    \bgetattr[(]settings,[ ]['"](\w+)['"]
    |
# Using a helper function. The first parameter is the request.
    \bget_config_value[(][^,]*, ['"](\w+)['"]
""", re.VERBOSE | re.UNICODE)

settings = set()
# Scan all files above the tools directory.
root_path = os.path.normpath(
    os.path.join(os.path.dirname(os.path.realpath(__file__)), ".."))
for directory, subdirs, files in os.walk(root_path):
    for filename in files:
        # Exclude all directories that start with a dot.
        subdirs[:] = (
            subdir for subdir in subdirs
            if not subdir.startswith(".")
        )
        # Only look at python files.
        if not filename.endswith(".py"):
            continue
        path = os.path.join(directory, filename)
        with open(path, 'r', encoding='utf-8') as f:
            data = f.read()
        # Look at all matches.
        for match in SETTINGS_RE.finditer(data):
            # Look at all captured groups.
            for group in match.groups():
                # Settings have to be non-empty and uppercase.
                if group and group.isupper():
                    settings.add(group)
print(sorted(settings))
