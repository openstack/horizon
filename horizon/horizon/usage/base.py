from __future__ import division

import datetime
import logging

from dateutil.relativedelta import relativedelta
from django.contrib import messages
from django.utils.translation import ugettext as _

from horizon import api
from horizon import exceptions
from horizon import forms
from horizon import time


LOG = logging.getLogger(__name__)


class BaseUsage(object):
    show_terminated = False

    def __init__(self, request, tenant_id=None):
        self.tenant_id = tenant_id or request.user.tenant_id
        self.request = request
        self.summary = {}
        self.usage_list = []

    @property
    def today(self):
        return time.today()

    @staticmethod
    def get_datetime(date, now=False):
        if now:
            now = time.utcnow()
            current_time = time.time(now.hour, now.minute, now.second)
        else:
            current_time = time.time()
        return datetime.datetime.combine(date, current_time)

    @staticmethod
    def get_start(year, month, day=1):
        return datetime.date(year, month, day)

    @staticmethod
    def get_end(year, month, day=1):
        period = relativedelta(months=1)
        date_end = BaseUsage.get_start(year, month, day) + period
        if date_end > time.today():
            date_end = time.today()
        return date_end

    def get_instances(self):
        instance_list = []
        [instance_list.extend(u.server_usages) for u in self.usage_list]
        return instance_list

    def get_date_range(self):
        if not hasattr(self, "start") or not hasattr(self, "end"):
            args = (self.today.year, self.today.month)
            form = self.get_form()
            if form.is_valid():
                args = (int(form.cleaned_data['year']),
                        int(form.cleaned_data['month']))
            self.start = self.get_start(*args)
            self.end = self.get_end(*args)
        return self.start, self.end

    def get_form(self):
        if not hasattr(self, 'form'):
            self.form = forms.DateForm(self.request.GET,
                                       initial={'year': self.today.year,
                                                'month': self.today.month})
        return self.form

    def get_usage_list(self, start, end):
        raise NotImplementedError("You must define a get_usage method.")

    def summarize(self, start, end):
        if start <= end <= time.today():
            # Convert to datetime.datetime just for API call.
            start = BaseUsage.get_datetime(start)
            end = BaseUsage.get_datetime(end, now=True)
            try:
                self.usage_list = self.get_usage_list(start, end)
            except:
                exceptions.handle(self.request,
                                  _('Unable to retrieve usage information.'))
        else:
            messages.info(self.request,
                          _("You are viewing data for the future, "
                            "which may or may not exist."))

        for tenant_usage in self.usage_list:
            tenant_summary = tenant_usage.get_summary()
            for key, value in tenant_summary.items():
                self.summary.setdefault(key, 0)
                self.summary[key] += value

    def csv_link(self):
        return "?date_month=%s&date_year=%s&format=csv" % self.get_date_range()


class GlobalUsage(BaseUsage):
    show_terminated = True

    def get_usage_list(self, start, end):
        return api.usage_list(self.request, start, end)


class TenantUsage(BaseUsage):
    attrs = ('memory_mb', 'vcpus', 'uptime',
             'hours', 'local_gb')

    def get_usage_list(self, start, end):
        show_terminated = self.request.GET.get('show_terminated',
                                               self.show_terminated)
        instances = []
        terminated_instances = []
        usage = api.usage_get(self.request, self.tenant_id, start, end)
        # Attribute may not exist if there are no instances
        if hasattr(usage, 'server_usages'):
            now = datetime.datetime.now()
            for server_usage in usage.server_usages:
                # This is a way to phrase uptime in a way that is compatible
                # with the 'timesince' filter. (Use of local time intentional.)
                server_uptime = server_usage['uptime']
                total_uptime = now - datetime.timedelta(seconds=server_uptime)
                server_usage['uptime_at'] = total_uptime
                if server_usage['ended_at'] and not show_terminated:
                    terminated_instances.append(server_usage)
                else:
                    instances.append(server_usage)
        usage.server_usages = instances
        return (usage,)
