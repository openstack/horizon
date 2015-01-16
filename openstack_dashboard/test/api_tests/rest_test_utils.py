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
import mock


def mock_obj_to_dict(r):
    return mock.Mock(**{'to_dict.return_value': r})


def construct_request(**args):
    mock_args = {
        'user.is_authenticated.return_value': True,
        'is_ajax.return_value': True,
        'policy.check.return_value': True,
        'body': ''
    }
    mock_args.update(args)
    return mock.Mock(**mock_args)
