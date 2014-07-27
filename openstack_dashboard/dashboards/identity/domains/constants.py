# Copyright 2013 Hewlett-Packard Development Company, L.P.
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

DOMAIN_INFO_FIELDS = ("name",
                      "description",
                      "enabled")
DOMAINS_INDEX_URL = 'horizon:identity:domains:index'
DOMAINS_INDEX_VIEW_TEMPLATE = 'identity/domains/index.html'
DOMAINS_CREATE_URL = 'horizon:identity:domains:create'
DOMAINS_UPDATE_URL = 'horizon:identity:domains:update'
DOMAIN_GROUP_MEMBER_SLUG = "update_group_members"
DOMAIN_USER_MEMBER_SLUG = "update_user_members"
