#    (c) Copyright 2014 Hewlett-Packard Development Company, L.P.
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

METADATA_CREATE_TEMPLATE = 'admin/metadata_defs/create.html'
METADATA_CREATE_URL = "horizon:admin:metadata_defs:create"
METADATA_UPDATE_TEMPLATE = 'admin/metadata_defs/update.html'
METADATA_UPDATE_URL = "horizon:admin:metadata_defs:update"
METADATA_DETAIL_OVERVIEW_TEMPLATE = "admin/metadata_defs/_detail_overview.html"
METADATA_DETAIL_CONTENTS_TEMPLATE = "admin/metadata_defs/_detail_contents.html"
METADATA_DETAIL_TEMPLATE = 'horizon/common/_detail.html'
METADATA_DETAIL_URL = "horizon:admin:metadata_defs:detail"
METADATA_INDEX_TEMPLATE = 'horizon/common/_data_table_view.html'
METADATA_INDEX_URL = 'horizon:admin:metadata_defs:index'
METADATA_MANAGE_RESOURCES_TEMPLATE = 'admin/metadata_defs/resource_types.html'
METADATA_MANAGE_RESOURCES_URL = 'horizon:admin:metadata_defs:resource_types'

METADEFS_PROTECTED_PROPS = ['created_at', 'updated_at', 'owner', 'schema']
