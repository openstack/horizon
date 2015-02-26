# Copyright (C) 2014 Universidad Politecnica de Madrid
#
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


class Idm(horizon.Dashboard):
    name = ("Identity Manager")
    name_sm = ("IdM")
    slug = "idm"
    panels = ('home', 'home_orgs', 'organizations', 
        'members', 'myApplications', 'users')
    default_panel = 'home'


    def nav(self, context):
        if (context['request'].organization.id 
            != context['request'].user.default_project_id):
            default_panel = 'home_orgs'
            return True
        else:
            default_panel = 'home'
            return True

horizon.register(Idm)
