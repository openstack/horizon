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

from glanceclient.common import exceptions as glance_exceptions
from keystoneclient import exceptions as keystone_exceptions
from novaclient import exceptions as nova_exceptions

from .utils import TestDataContainer


def data(TEST):
    TEST.exceptions = TestDataContainer()
    msg = "Expected failure."

    keystone_exception = keystone_exceptions.ClientException(500, message=msg)
    keystone_exception.silence_logging = True
    TEST.exceptions.keystone = keystone_exception

    nova_exception = nova_exceptions.ClientException(500, message=msg)
    nova_exception.silence_logging = True
    TEST.exceptions.nova = nova_exception

    glance_exception = glance_exceptions.ClientException(500, message=msg)
    glance_exception.silence_logging = True
    TEST.exceptions.glance = glance_exception
