# vim: tabstop=4 shiftwidth=4 softtabstop=4
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

from django.utils import text
from django.utils.translation import ugettext_lazy as _

from horizon import tables


def show_date(datum):
    return datum.split('T')[0]


class UsageTable(tables.DataTable):
    service = tables.Column('service', verbose_name=_('Service'))
    meter = tables.Column('meter', verbose_name=_('Meter'))
    description = tables.Column('description', verbose_name=_('Description'))
    time = tables.Column('time', verbose_name=_('Day'),
                         filters=[show_date])
    value = tables.Column('value', verbose_name=_('Value (Avg)'))

    def get_object_id(self, datum):
        return datum['time'] + datum['meter']

    # since these tables are dynamically created and named, we use title
    @property
    def name(self):
        # slugify was introduced in Django 1.5
        if hasattr(text, 'slugify'):
            return text.slugify(unicode(self.title))
        else:
            return self.title

    def __unicode__(self):
        return self.title

    class Meta:
        name = 'daily'
