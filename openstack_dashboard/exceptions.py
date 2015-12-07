# Copyright 2012 United States Government as represented by the
# Administrator of the National Aeronautics and Space Administration.
# All Rights Reserved.
#
# Copyright 2012 Nebula, Inc.
#
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

from cinderclient import exceptions as cinderclient
from glanceclient.common import exceptions as glanceclient
from heatclient import exc as heatclient
from keystoneclient import exceptions as keystoneclient
from neutronclient.common import exceptions as neutronclient
from novaclient import exceptions as novaclient
from requests import exceptions as requests
from swiftclient import client as swiftclient
from troveclient import exceptions as troveclient


UNAUTHORIZED = (
    keystoneclient.Unauthorized,
    cinderclient.Unauthorized,
    novaclient.Unauthorized,
    glanceclient.Unauthorized,
    neutronclient.Unauthorized,
    heatclient.HTTPUnauthorized,
    troveclient.Unauthorized,
)


NOT_FOUND = (
    keystoneclient.NotFound,
    cinderclient.NotFound,
    novaclient.NotFound,
    glanceclient.NotFound,
    neutronclient.NotFound,
    heatclient.HTTPNotFound,
    troveclient.NotFound,
)


# NOTE(gabriel): This is very broad, and may need to be dialed in.
RECOVERABLE = (
    keystoneclient.ClientException,
    # AuthorizationFailure is raised when Keystone is "unavailable".
    keystoneclient.AuthorizationFailure,
    keystoneclient.Forbidden,
    cinderclient.ClientException,
    cinderclient.ConnectionError,
    cinderclient.Forbidden,
    novaclient.ClientException,
    novaclient.Forbidden,
    glanceclient.ClientException,
    glanceclient.CommunicationError,
    neutronclient.Forbidden,
    neutronclient.NeutronClientException,
    swiftclient.ClientException,
    heatclient.HTTPForbidden,
    heatclient.HTTPException,
    troveclient.ClientException,
    requests.RequestException,
)
