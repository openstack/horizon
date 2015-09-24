# Copyright (c) 2014 eBay Software Foundation
# Copyright 2015 HP Software, LLC
# All Rights Reserved.
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

"""
Views for managing database clusters.
"""
from collections import OrderedDict
import logging

from django.core.urlresolvers import reverse
from django.core.urlresolvers import reverse_lazy
from django.utils.translation import ugettext_lazy as _

import six

from horizon import exceptions
from horizon import forms as horizon_forms
from horizon import tables as horizon_tables
from horizon import tabs as horizon_tabs
from horizon.utils import memoized

from openstack_dashboard.contrib.trove import api
from openstack_dashboard.contrib.trove.content.database_clusters import forms
from openstack_dashboard.contrib.trove.content.database_clusters import tables
from openstack_dashboard.contrib.trove.content.database_clusters import tabs


LOG = logging.getLogger(__name__)


class IndexView(horizon_tables.DataTableView):
    table_class = tables.ClustersTable
    template_name = 'project/database_clusters/index.html'

    def has_more_data(self, table):
        return self._more

    @memoized.memoized_method
    def get_flavors(self):
        try:
            flavors = api.trove.flavor_list(self.request)
        except Exception:
            flavors = []
            msg = _('Unable to retrieve database size information.')
            exceptions.handle(self.request, msg)
        return OrderedDict((six.text_type(flavor.id), flavor)
                           for flavor in flavors)

    def _extra_data(self, cluster):
        try:
            cluster_flavor = cluster.instances[0]["flavor"]["id"]
            flavors = self.get_flavors()
            flavor = flavors.get(cluster_flavor)
            if flavor is not None:
                cluster.full_flavor = flavor
        except Exception:
            # ignore any errors and just return cluster unaltered
            pass
        return cluster

    def get_data(self):
        marker = self.request.GET.get(
            tables.ClustersTable._meta.pagination_param)
        # Gather our clusters
        try:
            clusters = api.trove.cluster_list(self.request, marker=marker)
            self._more = clusters.next or False
        except Exception:
            self._more = False
            clusters = []
            msg = _('Unable to retrieve database clusters.')
            exceptions.handle(self.request, msg)

        map(self._extra_data, clusters)

        return clusters


class LaunchClusterView(horizon_forms.ModalFormView):
    form_class = forms.LaunchForm
    template_name = 'project/database_clusters/launch.html'
    success_url = reverse_lazy('horizon:project:database_clusters:index')


class DetailView(horizon_tabs.TabbedTableView):
    tab_group_class = tabs.ClusterDetailTabs
    template_name = 'horizon/common/_detail.html'
    page_title = "{{ cluster.name|default:cluster.id }}"

    def get_context_data(self, **kwargs):
        context = super(DetailView, self).get_context_data(**kwargs)
        context["url"] = reverse('horizon:project:database_clusters:index')
        context["cluster"] = self.get_data()
        return context

    @memoized.memoized_method
    def get_data(self):
        try:
            cluster_id = self.kwargs['cluster_id']
            cluster = api.trove.cluster_get(self.request, cluster_id)
        except Exception:
            redirect = reverse('horizon:project:database_clusters:index')
            msg = _('Unable to retrieve details '
                    'for database cluster: %s') % cluster_id
            exceptions.handle(self.request, msg, redirect=redirect)
        try:
            cluster.full_flavor = api.trove.flavor_get(
                self.request, cluster.instances[0]["flavor"]["id"])
        except Exception:
            LOG.error('Unable to retrieve flavor details'
                      ' for database cluster: %s' % cluster_id)
        cluster.num_instances = len(cluster.instances)

        # Todo(saurabhs) Set mgmt_url to dispaly Mgmt Console URL on
        # cluster details page
        # for instance in cluster.instances:
        #   if instance['type'] == "master":
        #       cluster.mgmt_url = "https://%s:5450/webui" % instance['ip'][0]

        return cluster

    def get_tabs(self, request, *args, **kwargs):
        cluster = self.get_data()
        return self.tab_group_class(request, cluster=cluster, **kwargs)


class AddShardView(horizon_forms.ModalFormView):
    form_class = forms.AddShardForm
    template_name = 'project/database_clusters/add_shard.html'
    success_url = reverse_lazy('horizon:project:database_clusters:index')
    page_title = _("Add Shard")

    def get_context_data(self, **kwargs):
        context = super(AddShardView, self).get_context_data(**kwargs)
        context["cluster_id"] = self.kwargs['cluster_id']
        return context

    def get_object(self, *args, **kwargs):
        if not hasattr(self, "_object"):
            cluster_id = self.kwargs['cluster_id']
            try:
                self._object = api.trove.cluster_get(self.request, cluster_id)
                # TODO(michayu): assumption that cluster is homogeneous
                flavor_id = self._object.instances[0]['flavor']['id']
                flavors = self.get_flavors()
                if flavor_id in flavors:
                    self._object.flavor_name = flavors[flavor_id].name
                else:
                    flavor = api.trove.flavor_get(self.request, flavor_id)
                    self._object.flavor_name = flavor.name
            except Exception:
                redirect = reverse("horizon:project:database_clusters:index")
                msg = _('Unable to retrieve cluster details.')
                exceptions.handle(self.request, msg, redirect=redirect)
        return self._object

    def get_flavors(self, *args, **kwargs):
        if not hasattr(self, "_flavors"):
            try:
                flavors = api.trove.flavor_list(self.request)
                self._flavors = OrderedDict([(str(flavor.id), flavor)
                                            for flavor in flavors])
            except Exception:
                redirect = reverse("horizon:project:database_clusters:index")
                exceptions.handle(
                    self.request,
                    _('Unable to retrieve flavors.'), redirect=redirect)
        return self._flavors

    def get_initial(self):
        initial = super(AddShardView, self).get_initial()
        _object = self.get_object()
        if _object:
            initial.update(
                {'cluster_id': self.kwargs['cluster_id'],
                 'name': getattr(_object, 'name', None)})
        return initial


class ResetPasswordView(horizon_forms.ModalFormView):
    form_class = forms.ResetPasswordForm
    template_name = 'project/database_clusters/reset_password.html'
    success_url = reverse_lazy('horizon:project:database_clusters:index')
    page_title = _("Reset Root Password")

    @memoized.memoized_method
    def get_object(self, *args, **kwargs):
        cluster_id = self.kwargs['cluster_id']
        try:
            return api.trove.cluster_get(self.request, cluster_id)
        except Exception:
            msg = _('Unable to retrieve cluster details.')
            redirect = reverse('horizon:project:database_clusters:index')
            exceptions.handle(self.request, msg, redirect=redirect)

    def get_context_data(self, **kwargs):
        context = super(ResetPasswordView, self).get_context_data(**kwargs)
        context['cluster_id'] = self.kwargs['cluster_id']
        return context

    def get_initial(self):
        return {'cluster_id': self.kwargs['cluster_id']}
