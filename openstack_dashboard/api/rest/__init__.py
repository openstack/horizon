# Copyright 2014, Rackspace, US, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""This package holds the REST API that supports the Horizon dashboard
Javascript code.

It is not intended to be used outside of Horizon, and makes no promises of
stability or fitness for purpose outside of that scope.

It does not promise to adhere to the general OpenStack API Guidelines set out
in https://wiki.openstack.org/wiki/APIChangeGuidelines.
"""

# import REST API modules here
from . import cinder       # noqa
from . import config       # noqa
from . import glance       # noqa
from . import heat         # noqa
from . import keystone     # noqa
from . import network      # noqa
from . import neutron      # noqa
from . import nova         # noqa
from . import policy       # noqa
from . import swift        # noqa
