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

from django.contrib.humanize.templatetags import humanize
from django.utils import text
from django.utils.translation import ugettext_lazy as _

from horizon import tables


def show_date(datum):
    return datum.split('T')[0]


class ModifyUsageReportParameters(tables.LinkAction):
    name = "create"
    verbose_name = _("Modify Usage Report Parameters")
    url = "horizon:admin:metering:create"
    classes = ("ajax-modal",)
    icon = "edit"


class CreateCSVUsageReport(tables.LinkAction):
    name = "csv"
    verbose_name = _("Download CSV Summary")
    url = "horizon:admin:metering:csvreport"
    classes = ("btn-create",)
    icon = "download"


class ReportTable(tables.DataTable):
    project = tables.Column('project', verbose_name=_('Project'))
    service = tables.Column('service', verbose_name=_('Service'))
    meter = tables.Column('meter', verbose_name=_('Meter'))
    description = tables.Column('description', verbose_name=_('Description'))
    time = tables.Column('time', verbose_name=_('Day'),
                         filters=[show_date])
    value = tables.Column('value', verbose_name=_('Value (Avg)'),
                          filters=[humanize.intcomma])
    unit = tables.Column('unit', verbose_name=_('Unit'))

    def get_object_id(self, obj):
        return "%s-%s-%s" % (obj['project'], obj['service'], obj['meter'])

    class Meta(object):
        name = 'report_table'
        verbose_name = _("Daily Usage Report")
        table_actions = (ModifyUsageReportParameters, CreateCSVUsageReport)
        multi_select = False


class UsageTable(tables.DataTable):
    service = tables.Column('service', verbose_name=_('Service'))
    meter = tables.Column('meter', verbose_name=_('Meter'))
    description = tables.Column('description', verbose_name=_('Description'))
    time = tables.Column('time', verbose_name=_('Day'),
                         filters=[show_date])
    value = tables.Column('value', verbose_name=_('Value (Avg)'),
                          filters=[humanize.intcomma])

    def __init__(self, request, *args, **kwargs):
        super(UsageTable, self).__init__(request, *args, **kwargs)
        self.title = getattr(self, 'title', None)

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

    class Meta(object):
        name = 'daily'
