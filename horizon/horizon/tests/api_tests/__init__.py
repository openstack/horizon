# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright 2011 United States Government as represented by the
# Administrator of the National Aeronautics and Space Administration.
# All Rights Reserved.
#
# Copyright 2011 Nebula, Inc.
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

from horizon.tests.api_tests.base import (APIResourceWrapperTests,
        APIDictWrapperTests, ApiHelperTests)
from horizon.tests.api_tests.glance import GlanceApiTests, ImageWrapperTests
from horizon.tests.api_tests.keystone import (KeystoneAdminApiTests,
        TokenApiTests, RoleAPITests, TenantAPITests, UserAPITests)
from horizon.tests.api_tests.nova import (ServerWrapperTests,
        ComputeApiTests, ExtrasApiTests, VolumeTests, APIExtensionTests)
from horizon.tests.api_tests.swift import SwiftApiTests
