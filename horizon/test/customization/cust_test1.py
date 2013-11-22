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

import horizon
from horizon import base

# Rename "cats" to "wildcats", ignore if panel doesn't exist
try:
    cats = horizon.get_dashboard("cats")
    cats.name = "WildCats"
except base.NotRegistered:
    cats = None

# Disable tigers panel, ignore if panel doesn't exist
if cats:
    try:
        tigers = cats.get_panel("tigers")
        cats.unregister(tigers.__class__)
    except base.NotRegistered:
        pass

# Remove dogs dashboard, ignore if dashboard doesn't exist
try:
    dogs = horizon.get_dashboard("dogs")
    horizon.unregister(dogs.__class__)
except base.NotRegistered:
    pass
