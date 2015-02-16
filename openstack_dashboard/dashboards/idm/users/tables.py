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

import logging

from django.core import urlresolvers
from django.utils.translation import ugettext_lazy as _

from horizon import tables


LOG = logging.getLogger('idm_logger')

class OrganizationsTable(tables.DataTable):
    name = tables.Column('name', verbose_name=_('Name'))
    description = tables.Column(lambda obj: getattr(obj, 'description', None),
                                verbose_name=_('Description'))
    clickable = True
    switch = True
    show_avatar = True

    class Meta:
        name = "organizations"
        verbose_name = _("Organizations")


class ApplicationsTable(tables.DataTable):
    name = tables.Column('name', verbose_name=_('Applications'))
    clickable = True
    show_avatar = True

    class Meta:
        name = "applications"
        verbose_name = _("Applications")
