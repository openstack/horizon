# vim: tabstop=4 shiftwidth=4 softtabstop=4

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
from keystoneclient import exceptions as keystoneclient
from novaclient import exceptions as novaclient
from quantumclient.common import exceptions as quantumclient
from swiftclient import client as swiftclient


UNAUTHORIZED = (keystoneclient.Unauthorized,
                keystoneclient.Forbidden,
                cinderclient.Unauthorized,
                cinderclient.Forbidden,
                novaclient.Unauthorized,
                novaclient.Forbidden,
                glanceclient.Unauthorized,
                quantumclient.Unauthorized,
                quantumclient.Forbidden)

NOT_FOUND = (keystoneclient.NotFound,
             cinderclient.NotFound,
             novaclient.NotFound,
             glanceclient.NotFound,
             quantumclient.NetworkNotFoundClient,
             quantumclient.PortNotFoundClient)

# NOTE(gabriel): This is very broad, and may need to be dialed in.
RECOVERABLE = (keystoneclient.ClientException,
               # AuthorizationFailure is raised when Keystone is "unavailable".
               keystoneclient.AuthorizationFailure,
               cinderclient.ClientException,
               novaclient.ClientException,
               glanceclient.ClientException,
               # NOTE(amotoki): Quantum exceptions other than the first one
               # are recoverable in many cases (e.g., NetworkInUse is not
               # raised once VMs which use the network are terminated).
               quantumclient.QuantumClientException,
               quantumclient.NetworkInUseClient,
               quantumclient.PortInUseClient,
               quantumclient.AlreadyAttachedClient,
               quantumclient.StateInvalidClient,
               swiftclient.ClientException)
