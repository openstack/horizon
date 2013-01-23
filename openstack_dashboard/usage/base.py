from __future__ import division

from calendar import monthrange
import datetime
import logging

from django.utils.translation import ugettext as _
from django.utils import timezone

from horizon import exceptions
from horizon import forms
from horizon import messages

from openstack_dashboard import api
from openstack_dashboard.usage import quotas


LOG = logging.getLogger(__name__)


def almost_now(input_time):
    now = timezone.make_naive(timezone.now(), timezone.utc)
    # If we're less than a minute apart we'll assume success here.
    return now - input_time < datetime.timedelta(seconds=30)


class BaseUsage(object):
    show_terminated = False

    def __init__(self, request, tenant_id=None):
        self.tenant_id = tenant_id or request.user.tenant_id
        self.request = request
        self.summary = {}
        self.usage_list = []
        self.quotas = {}

    @property
    def today(self):
        return timezone.now()

    @staticmethod
    def get_start(year, month, day=1):
        start = datetime.datetime(year, month, day, 0, 0, 0)
        return timezone.make_aware(start, timezone.utc)

    @staticmethod
    def get_end(year, month, day=1):
        days_in_month = monthrange(year, month)[1]
        period = datetime.timedelta(days=days_in_month)
        end = BaseUsage.get_start(year, month, day) + period
        # End our calculation at midnight of the given day.
        date_end = datetime.datetime.combine(end, datetime.time(0, 0, 0))
        date_end = timezone.make_aware(date_end, timezone.utc)
        if date_end > timezone.now():
            date_end = timezone.now()
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
            if any(key in ['month', 'year'] for key in self.request.GET):
                # bound form
                self.form = forms.DateForm(self.request.GET)
            else:
                # non-bound form
                self.form = forms.DateForm(initial={'month': self.today.month,
                                                    'year': self.today.year})
        return self.form

    def get_usage_list(self, start, end):
        raise NotImplementedError("You must define a get_usage method.")

    def summarize(self, start, end):
        if start <= end <= self.today:
            # The API can't handle timezone aware datetime, so convert back
            # to naive UTC just for this last step.
            start = timezone.make_naive(start, timezone.utc)
            end = timezone.make_naive(end, timezone.utc)
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

    def get_quotas(self):
        try:
            self.quotas = quotas.tenant_quota_usages(self.request)
        except:
            exceptions.handle(self.request,
                              _("Unable to retrieve quota information."))

    def csv_link(self):
        form = self.get_form()
        if hasattr(form, "cleaned_data"):
            data = form.cleaned_data
        else:
            data = {"month": self.today.month, "year": self.today.year}
        return "?month=%s&year=%s&format=csv" % (data['month'], data['year'])


class GlobalUsage(BaseUsage):
    show_terminated = True

    def get_usage_list(self, start, end):
        return api.nova.usage_list(self.request, start, end)


class TenantUsage(BaseUsage):
    attrs = ('memory_mb', 'vcpus', 'uptime',
             'hours', 'local_gb')

    def get_usage_list(self, start, end):
        show_terminated = self.request.GET.get('show_terminated',
                                               self.show_terminated)
        instances = []
        terminated_instances = []
        usage = api.nova.usage_get(self.request, self.tenant_id, start, end)
        # Attribute may not exist if there are no instances
        if hasattr(usage, 'server_usages'):
            now = self.today
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
