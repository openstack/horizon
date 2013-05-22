# vim: tabstop=4 shiftwidth=4 softtabstop=4

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

from heatclient.v1.stacks import Stack, StackManager

from .utils import TestDataContainer


def data(TEST):
    TEST.stacks = TestDataContainer()

    # Stacks
    stack1 = {
        "description": "No description",
        "links": [{
            "href": "http://192.168.1.70:8004/v1/"
                    "051c727ee67040d6a7b7812708485a97/"
                    "stacks/stack-1211-38/"
                    "05b4f39f-ea96-4d91-910c-e758c078a089",
            "rel": "self"
        }],
        "stack_status_reason": "Stack successfully created",
        "stack_name": "stack-1211-38",
        "creation_time": "2013-04-22T00:11:39Z",
        "updated_time": "2013-04-22T00:11:39Z",
        "stack_status": "CREATE_COMPLETE",
        "id": "05b4f39f-ea96-4d91-910c-e758c078a089"
    }
    stack = Stack(StackManager(None), stack1)
    TEST.stacks.add(stack)
