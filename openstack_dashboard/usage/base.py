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

from __future__ import division

import datetime

from django.conf import settings
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _

from horizon import exceptions
from horizon import forms
from horizon import messages

from openstack_dashboard import api


class BaseUsage(object):
    show_deleted = False

    def __init__(self, request, project_id=None):
        self.project_id = project_id or request.user.tenant_id
        self.request = request
        self.summary = {}
        self.usage_list = []
        self.limits = {}
        self.quotas = {}

    @property
    def today(self):
        return timezone.now()

    @property
    def first_day(self):
        days_range = getattr(settings, 'OVERVIEW_DAYS_RANGE', 1)
        if days_range:
            return self.today.date() - datetime.timedelta(days=days_range)
        else:
            return datetime.date(self.today.year, self.today.month, 1)

    @staticmethod
    def get_start(year, month, day):
        start = datetime.datetime(year, month, day, 0, 0, 0)
        return timezone.make_aware(start, timezone.utc)

    @staticmethod
    def get_end(year, month, day):
        end = datetime.datetime(year, month, day, 23, 59, 59)
        return timezone.make_aware(end, timezone.utc)

    def get_instances(self):
        instance_list = []
        [instance_list.extend(u.server_usages) for u in self.usage_list]
        return instance_list

    def get_date_range(self):
        if not hasattr(self, "start") or not hasattr(self, "end"):
            args_start = (self.first_day.year, self.first_day.month,
                          self.first_day.day)
            args_end = (self.today.year, self.today.month, self.today.day)
            form = self.get_form()
            if form.is_valid():
                start = form.cleaned_data['start']
                end = form.cleaned_data['end']
                args_start = (start.year,
                              start.month,
                              start.day)
                args_end = (end.year,
                            end.month,
                            end.day)
            elif form.is_bound:
                messages.error(self.request,
                               _("Invalid date format: "
                                 "Using today as default."))
            self.start = self.get_start(*args_start)
            self.end = self.get_end(*args_end)
        return self.start, self.end

    def init_form(self):
        self.start = self.first_day
        self.end = self.today.date()

        return self.start, self.end

    def get_form(self):
        if not hasattr(self, 'form'):
            req = self.request
            start = req.GET.get('start', req.session.get('usage_start'))
            end = req.GET.get('end', req.session.get('usage_end'))
            if start and end:
                # bound form
                self.form = forms.DateForm({'start': start, 'end': end})
            else:
                # non-bound form
                init = self.init_form()
                start = init[0].isoformat()
                end = init[1].isoformat()
                self.form = forms.DateForm(initial={'start': start,
                                                    'end': end})
            req.session['usage_start'] = start
            req.session['usage_end'] = end
        return self.form

    def _get_neutron_usage(self, limits, resource_name):
        resource_map = {
            'floatingip': {
                'api': api.neutron.tenant_floating_ip_list,
                'limit_name': 'totalFloatingIpsUsed',
                'message': _('Unable to retrieve floating IP addresses.')
            },
            'security_group': {
                'api': api.neutron.security_group_list,
                'limit_name': 'totalSecurityGroupsUsed',
                'message': _('Unable to retrieve security groups.')
            }
        }

        resource = resource_map[resource_name]
        try:
            method = resource['api']
            current_used = len(method(self.request))
        except Exception:
            current_used = 0
            msg = resource['message']
            exceptions.handle(self.request, msg)

        limits[resource['limit_name']] = current_used

    def _set_neutron_limit(self, limits, neutron_quotas, resource_name):
        limit_name_map = {
            'floatingip': 'maxTotalFloatingIps',
            'security_group': 'maxSecurityGroups',
        }
        if neutron_quotas is None:
            resource_max = float("inf")
        else:
            resource_max = getattr(neutron_quotas.get(resource_name),
                                   'limit', float("inf"))
            if resource_max == -1:
                resource_max = float("inf")

        limits[limit_name_map[resource_name]] = resource_max

    def get_neutron_limits(self):
        if not api.base.is_service_enabled(self.request, 'network'):
            return
        try:
            neutron_quotas_supported = (
                api.neutron.is_quotas_extension_supported(self.request))
            neutron_sg_used = (
                api.neutron.is_extension_supported(self.request,
                                                   'security-group'))
            if api.neutron.floating_ip_supported(self.request):
                self._get_neutron_usage(self.limits, 'floatingip')
            if neutron_sg_used:
                self._get_neutron_usage(self.limits, 'security_group')
            # Quotas are an optional extension in Neutron. If it isn't
            # enabled, assume the floating IP limit is infinite.
            if neutron_quotas_supported:
                neutron_quotas = api.neutron.tenant_quota_get(self.request,
                                                              self.project_id)
            else:
                neutron_quotas = None
        except Exception:
            # Assume neutron security group and quotas are enabled
            # because they are enabled in most Neutron plugins.
            neutron_sg_used = True
            neutron_quotas = None
            msg = _('Unable to retrieve network quota information.')
            exceptions.handle(self.request, msg)

        self._set_neutron_limit(self.limits, neutron_quotas, 'floatingip')
        if neutron_sg_used:
            self._set_neutron_limit(self.limits, neutron_quotas,
                                    'security_group')

    def get_cinder_limits(self):
        """Get volume limits if cinder is enabled."""
        if not api.cinder.is_volume_service_enabled(self.request):
            return
        try:
            self.limits.update(api.cinder.tenant_absolute_limits(self.request))
        except Exception:
            msg = _("Unable to retrieve volume limit information.")
            exceptions.handle(self.request, msg)

        return

    def get_limits(self):
        try:
            self.limits = api.nova.tenant_absolute_limits(self.request,
                                                          reserved=True)
        except Exception:
            exceptions.handle(self.request,
                              _("Unable to retrieve limit information."))
        self.get_neutron_limits()
        self.get_cinder_limits()

    def get_usage_list(self, start, end):
        return []

    def summarize(self, start, end):
        if not api.nova.extension_supported('SimpleTenantUsage', self.request):
            return

        if start <= end and start <= self.today:
            # The API can't handle timezone aware datetime, so convert back
            # to naive UTC just for this last step.
            start = timezone.make_naive(start, timezone.utc)
            end = timezone.make_naive(end, timezone.utc)
            try:
                self.usage_list = self.get_usage_list(start, end)
            except Exception:
                exceptions.handle(self.request,
                                  _('Unable to retrieve usage information.'))
        elif end < start:
            messages.error(self.request,
                           _("Invalid time period. The end date should be "
                             "more recent than the start date."))
        elif start > self.today:
            messages.error(self.request,
                           _("Invalid time period. You are requesting "
                             "data from the future which may not exist."))

        for project_usage in self.usage_list:
            project_summary = project_usage.get_summary()
            for key, value in project_summary.items():
                self.summary.setdefault(key, 0)
                self.summary[key] += value

    def csv_link(self):
        form = self.get_form()
        data = {}
        if hasattr(form, "cleaned_data"):
            data = form.cleaned_data
        if not ('start' in data and 'end' in data):
            data = {"start": self.today.date(), "end": self.today.date()}
        return "?start=%s&end=%s&format=csv" % (data['start'],
                                                data['end'])


class GlobalUsage(BaseUsage):
    show_deleted = True

    def get_usage_list(self, start, end):
        return api.nova.usage_list(self.request, start, end)


class ProjectUsage(BaseUsage):
    attrs = ('memory_mb', 'vcpus', 'uptime',
             'hours', 'local_gb')

    def get_usage_list(self, start, end):
        show_deleted = self.request.GET.get('show_deleted',
                                            self.show_deleted)
        instances = []
        deleted_instances = []
        usage = api.nova.usage_get(self.request, self.project_id, start, end)
        # Attribute may not exist if there are no instances
        if hasattr(usage, 'server_usages'):
            now = self.today
            for server_usage in usage.server_usages:
                # This is a way to phrase uptime in a way that is compatible
                # with the 'timesince' filter. (Use of local time intentional.)
                server_uptime = server_usage['uptime']
                total_uptime = now - datetime.timedelta(seconds=server_uptime)
                server_usage['uptime_at'] = total_uptime
                if server_usage['ended_at'] and not show_deleted:
                    deleted_instances.append(server_usage)
                else:
                    instances.append(server_usage)
        usage.server_usages = instances
        return (usage,)
