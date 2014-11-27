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

def filter_default_organizations(projects):
    """ Remove from a list the automated created project for a user. This project
    is created during the user registration step and is needed for the user to be
    able to perform operations in the cloud, as a work around the Keystone-OpenStack
    project behaviour. We don't want the user to be able to do any operations to this 
    project nor even notice it exists.
    """
    return [p for p in projects if not getattr(p, 'is_default', False)]