# vim: tabstop=4 shiftwidth=4 softtabstop=4
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

from ceilometerclient import client as ceilometer_client
from django.conf import settings  # noqa

from openstack_dashboard.api import base
from openstack_dashboard.api import keystone

LOG = logging.getLogger(__name__)


def is_iterable(var):
    """ Return True if the given is list or tuple.
    """

    return (isinstance(var, (list, tuple)) or
        issubclass(var.__class__, (list, tuple)))


def make_query(user_id=None, tenant_id=None, resource_id=None):
    """ Returns query built form given parameters.

    This query can be then used for querying resources, meters and
    statistics.

    :Parameters:
      - `user_id`: user_id or list of user_ids
      - `tenant_id`: tenant_id or list of tenant_ids
      - `resource_id`: resource_id or list of resource_ids
    """

    query = []
    if user_id and user_id != 'None':
        if is_iterable(user_id):
            for u_id in user_id:
                query.append({"field": "user_id", "op": "eq", "value": u_id})
        else:
            query.append({"field": "user_id", "op": "eq", "value": user_id})

    if tenant_id and tenant_id != 'None':
        if is_iterable(tenant_id):
            for t_id in tenant_id:
                query.append({"field": "project_id", "op": "eq",
                              "value": t_id})
        else:
            query.append({"field": "project_id", "op": "eq",
                          "value": tenant_id})

    if resource_id and resource_id != 'None':
        if is_iterable(resource_id):
            for r_id in resource_id:
                query.append({"field": "resource_id", "op": "eq",
                              "value": r_id})
        else:
            query.append({"field": "resource_id", "op": "eq",
                          "value": resource_id})
    return query


class Meter(base.APIResourceWrapper):
    """ Represents one Ceilometer meter.
    """
    _attrs = ['name', 'type', 'unit', 'resource_id', 'user_id',
              'project_id']


class Resource(base.APIResourceWrapper):
    """ Represents one Ceilometer resource.
    """
    _attrs = ['resource_id', 'source', 'user_id', 'project_id', 'metadata',
              'links']

    def __init__(self, apiresource, ceilometer_usage=None):
        super(Resource, self).__init__(apiresource)

        # TODO(lsmola) make parallel obtaining of tenant and user
        # make the threading here, thread join into resource_list
        self._id = "%s__%s__%s" % (self.project_id,
                                   self.user_id,
                                   self.resource_id)

        if ceilometer_usage and self.project_id:
            self._tenant = ceilometer_usage.get_tenant(self.project_id)
        else:
            self._tenant = None

        if ceilometer_usage and self.user_id:
            self._user = ceilometer_usage.get_user(self.user_id)
        else:
            self._user = None

        self._query = make_query(tenant_id=self.project_id,
                                 user_id=self.user_id,
                                 resource_id=self.resource_id)

    @property
    def name(self):
        name = self.metadata.get("name", None)
        display_name = self.metadata.get("display_name", None)
        return name or display_name or ""

    @property
    def id(self):
        return self._id

    @property
    def tenant(self):
        return self._tenant

    @property
    def user(self):
        return self._user

    @property
    def resource(self):
        return self.resource_id

    @property
    def query(self):
        return self._query


class ResourceAggregate(Resource):
    """ Represents aggregate of more resources together.

    Aggregate of resources can be obtain by specifing
    multiple ids in one parameter or by not specifying
    one parameter.
    Or it can be specified by query directly.

    Example:
        We obtain can have aggregate of resources by specifying
        multiple resource_ids in resource_id parameter in init.
        Or we can specify only tenant_id, which will return
        all resources of that tenant.
    """

    def __init__(self, tenant_id=None, user_id=None, resource_id=None,
                 ceilometer_usage=None, query=None, identifier=None):

        self._id = identifier

        self.tenant_id = None
        self.user_id = None
        self.resource_id = None

        if query:

            self._query = query
        else:
            # TODO(lsmola) make parallel obtaining of tenant and user
            # make the threading here, thread join into resource_list
            if (ceilometer_usage and tenant_id and
                    not is_iterable(tenant_id)):
                self.tenant_id = tenant_id
                self._tenant = ceilometer_usage.get_tenant(tenant_id)
            else:
                self._tenant = None

            if (ceilometer_usage and user_id and
                    not is_iterable(user_id)):
                self.user_id = user_id
                self._user = ceilometer_usage.get_user(user_id)
            else:
                self._user = None

            if not is_iterable(resource_id):
                self.resource_id = resource_id

            self._query = make_query(tenant_id=tenant_id,
                                     user_id=user_id,
                                     resource_id=resource_id)

    @property
    def id(self):
        return self._id


class Sample(base.APIResourceWrapper):
    """ Represents one Ceilometer sample.
    """

    _attrs = ['counter_name', 'user_id', 'resource_id', 'timestamp',
              'resource_metadata', 'source', 'counter_unit', 'counter_volume',
              'project_id', 'counter_type', 'resource_metadata']

    @property
    def instance(self):
        display_name = self.resource_metadata.get('display_name', None)
        instance_id = self.resource_metadata.get('instance_id', None)
        return display_name or instance_id

    @property
    def name(self):
        name = self.resource_metadata.get("name", None)
        display_name = self.resource_metadata.get("display_name", None)
        return name or display_name or ""


class Statistic(base.APIResourceWrapper):
    """ Represents one Ceilometer statistic.
    """

    _attrs = ['period', 'period_start', 'period_end',
              'count', 'min', 'max', 'sum', 'avg',
              'duration', 'duration_start', 'duration_end']


class GlobalDiskUsage(base.APIResourceWrapper):
    """ Represents collection of resources with statistic of defined meters.

        Resources are filtered either by given default query or by
        meters in python. It's preferred to use default_query as it is more
        effective.
    """

    _attrs = ["id", "tenant", "user", "resource", "disk_read_bytes",
              "disk_read_requests", "disk_write_bytes",
              "disk_write_requests"]

    meters = ["disk.read.bytes",
              "disk.read.requests",
              "disk.write.bytes",
              "disk.write.requests"]

    default_query = [{"field": "metadata.OS-EXT-AZ:availability_zone",
                      "op": "eq",
                      "value": "nova"}]
    stats_attr = "avg"


class GlobalNetworkTrafficUsage(base.APIResourceWrapper):
    """ Represents collection of resources with statistic of defined meters.

        Resources are filtered either by given default query or by
        meters in python. It's preferred to use default_query as it is more
        effective.
    """

    _attrs = ["id", "tenant", "user", "resource", "network_incoming_bytes",
              "network_incoming_packets", "network_outgoing_bytes",
              "network_outgoing_packets"]

    meters = ["network.incoming.bytes",
              "network.incoming.packets",
              "network.outgoing.bytes",
              "network.outgoing.packets"]

    # TODO(lsmola) once the API will support it need to add default query,
    # instead of filtering resources in python by the filter_func
    default_query = None
    stats_attr = "avg"


class GlobalNetworkUsage(base.APIResourceWrapper):
    """ Represents collection of resources with statistic of defined meters.

        Resources are filtered either by given default query or by
        meters in python. It's preferred to use default_query as it is more
        effective.
    """

    _attrs = ["id", "tenant", "user", "resource", "network", "network_create",
              "subnet", "subnet_create", "port", "port_create", "router",
              "router_create", "ip_floating", "ip_floating_create"]

    meters = ["network", "network_create",
              "subnet", "subnet_create",
              "port", "port_create",
              "router", "router_create",
              "ip_floating", "ip_floating_create"]

    # TODO(lsmola) once the API will support it need to add default query,
    # instead of filtering resources in python by the filter_func
    default_query = None
    stats_attr = "max"


class GlobalObjectStoreUsage(base.APIResourceWrapper):
    """ Represents collection of resources with statistic of defined meters.

        Resources are filtered either by given default query or by
        meters in python. It's preferred to use default_query as it is more
        effective.
    """

    _attrs = ["id", "tenant", "user", "resource", "storage_objects",
              "storage_objects_size", "storage_objects_outgoing_bytes",
              "storage_objects_incoming_bytes"]

    meters = ["storage.objects",
              "storage.objects.size",
              "storage.objects.incoming.bytes",
              "storage.objects.outgoing.bytes"]

    # TODO(lsmola) once the API will support it need to add default query,
    # instead of filtering resources in python by the filter_func
    default_query = None
    stats_attr = "avg"


def ceilometerclient(request):
    """ Initialization of Ceilometer client.
    """

    endpoint = base.url_for(request, 'metering')
    insecure = getattr(settings, 'OPENSTACK_SSL_NO_VERIFY', False)
    cacert = getattr(settings, 'OPENSTACK_SSL_CACERT', None)
    LOG.debug('ceilometerclient connection created using token "%s" '
              'and endpoint "%s"' % (request.user.token.id, endpoint))
    return ceilometer_client.Client('2', endpoint,
                                    token=(lambda: request.user.token.id),
                                    insecure=insecure,
                                    ca_file=cacert)


def resource_list(request, query=None, ceilometer_usage_object=None):
    """List the resources."""
    resources = ceilometerclient(request).\
        resources.list(q=query)
    return [Resource(r, ceilometer_usage_object) for r in resources]


def sample_list(request, meter_name, query=None):
    """List the samples for this meters."""
    samples = ceilometerclient(request).samples.list(meter_name=meter_name,
                                                     q=query)
    return [Sample(s) for s in samples]


def meter_list(request, query=None):
    """List the user's meters."""
    meters = ceilometerclient(request).meters.list(query)
    return [Meter(m) for m in meters]


def statistic_list(request, meter_name, query=None, period=None):
    """List of statistics."""
    statistics = ceilometerclient(request).\
        statistics.list(meter_name=meter_name, q=query, period=period)
    return [Statistic(s) for s in statistics]


class CeilometerUsage(object):
    """ Represents wrapper of any Ceilometer queries.

    One instance of this class should be shared between resources
    as this class provides a place where users and tenants are
    cached. So there are no duplicate queries to API.

    This class also wraps Ceilometer API calls and provides parallel
    HTTP calls to API.
    """

    def __init__(self, request):
        self._request = request

        # Cached users and tenants.
        self._users = {}
        self._tenants = {}

    def get_user(self, user_id):
        """ Returns user fetched form API

        Caching the result, so it doesn't contact API twice with the
        same query
        """

        user = self._users.get(user_id, None)
        if not user:
            user = keystone.user_get(self._request, user_id)
            # caching the user, for later use
            self._users[user_id] = user
        return user

    def preload_all_users(self):
        """ Preloads all users into dictionary.

        It's more effective to preload all users, rather the fetching many
        users by separate API get calls.
        """

        users = keystone.user_list(self._request)
        # Cache all users on right indexes, this is more effective than to
        # obtain large number of users one by one by keystone.user_get
        for u in users:
            self._users[u.id] = u

    def get_tenant(self, tenant_id):
        """ Returns tenant fetched form API

        Caching the result, so it doesn't contact API twice with the
        same query
        """

        tenant = self._tenants.get(tenant_id, None)
        if not tenant:
            tenant = keystone.tenant_get(self._request, tenant_id)
            # caching the tenant for later use
            self._tenants[tenant_id] = tenant
        return tenant

    def preload_all_tenants(self):
        """ Preloads all teannts into dictionary.

        It's more effective to preload all tenants, rather the fetching many
        tenants by separate API get calls.
        """

        tenants = keystone.tenant_list(self._request)
        # Cache all tenants on right indexes, this is more effective than to
        # obtain large number of tenants one by one by keystone.tenant_get
        for t in tenants:
            self._users[t.id] = t

    def global_data_get(self, used_cls=None, query=None,
                        with_statistics=False, additional_query=None,
                        with_users_and_tenants=True):
        """ Obtaining a resources for table view.

        It obtains resources with statistics data according to declaration
        in used_cls class.

        :Parameters:
          - `user_cls`: Class wrapper from global data. It acts as wrapper for
                        settings needed. See the call of this method for
                        details.
          - `query`: Explicit query definition for fetching a resources. if
                     no query is provided, it takes default_query from
                     used_cls. If no default query is provided, it fetches
                     all the resources and filters them by meters defined
                     in used_cls.
          - `with_statistic`: Define whether statistics data from the meters
                              defined in used_cls should be fetched.
                              Can be used to first obtain only the pure
                              resources, then fetch the statistics data by
                              AJAX.
          - `additional_query`: Additional query for the statistics.
                                Eg. timespan, etc.
          - `with_users_and_tenants`: If true a user and a tenant object will
                                      be added to each resource object.
        """

        default_query = used_cls.default_query
        query = query or default_query
        filter_func = None

        def filter_resources(resource):
            """ Method for filtering resources by theirs links.rel attr.

                The links.rel attributes contains all meters the resource
                have.
            """
            for link in resource.links:
                if link['rel'] in used_cls.meters:
                    return True
            return False

        if not query:
            # Not all resource types can be obtain by query, if there is not
            # a query, we are filtering all resources by this function.
            filter_func = filter_resources

        if with_statistics:
            # Will add statistic data into resources.
            resources = self.resources_with_statistics(
                query,
                used_cls.meters,
                filter_func=filter_func,
                stats_attr=used_cls.stats_attr,
                additional_query=additional_query,
                with_users_and_tenants=with_users_and_tenants)
        else:
            # Will load only resources without statistical data.
            resources = self.resources(query, filter_func=filter_func,
                with_users_and_tenants=with_users_and_tenants)

        return [used_cls(resource) for resource in resources]

    def global_disk_usage(self, query=None, with_statistics=False,
                          additional_query=None):
        """  Wrapper for specific call of global_data_get.
        """

        return self.global_data_get(used_cls=GlobalDiskUsage,
                                    query=query,
                                    with_statistics=with_statistics,
                                    additional_query=additional_query)

    def global_network_traffic_usage(self, query=None, with_statistics=False,
                                     additional_query=None):
        """  Wrapper for specific call of global_data_get.
        """

        return self.global_data_get(used_cls=GlobalNetworkTrafficUsage,
                                    query=query,
                                    with_statistics=with_statistics,
                                    additional_query=additional_query)

    def global_network_usage(self, query=None, with_statistics=False,
                             additional_query=None):
        """  Wrapper for specific call of global_data_get.
        """

        return self.global_data_get(used_cls=GlobalNetworkUsage,
                                    query=query,
                                    with_statistics=with_statistics,
                                    additional_query=additional_query)

    def global_object_store_usage(self, query=None, with_statistics=False,
                                  additional_query=None):
        """  Wrapper for specific call of global_data_get.
        """

        return self.global_data_get(used_cls=GlobalObjectStoreUsage,
                                    query=query,
                                    with_statistics=with_statistics,
                                    additional_query=additional_query)

    def query_from_object_id(self, object_id):
        """ Obtaining a query from resource id.

        Query can be then used to identify a resource in resources or meters
        calls. ID is being built in the Resource initializer, or returned by
        Datatable into UpdateRow functionality.
        """
        try:
            tenant_id, user_id, resource_id = object_id.split("__")
        except ValueError:
            return []

        return make_query(tenant_id=tenant_id, user_id=user_id,
                          resource_id=resource_id)

    def update_with_statistics(self, resource, meter_names, period=None,
                               stats_attr=None, additional_query=None):
        """ Adding statistical data into one Resource or ResourceAggregate.

        It adds each statistic of each meter into the resource attributes.
        Attribute name is the meter name with replaced '.' to '_'.

        :Parameters:
          - `resource`: Resource or ResourceAggregate object, that will
                        be filled by statistic data.
          - `meter_names`: List of meter names of which we want the
                           statistics.
          - `period`: In seconds. If no period is given, only one aggregate
                      statistic is returned. If given a faceted result will be
                      returned, dividend into given periods. Periods with no
                      data are ignored.
          - `stats_attr`: String representing the attribute name of the stats.
                          Eg. (avg, max, min...) If None is given, whole
                          statistic object is returned,
          - `additional_query`: Additional query for the statistics.
                                Eg. timespan, etc.
        """

        # query for identifying one resource in meters
        query = resource.query
        if additional_query:
            if not is_iterable(additional_query):
                raise ValueError("Additional query must be list of"
                                 " conditions. See the docs for format.")
            query = query + additional_query

        # TODO(lsmola) maybe a thread for each meter?
        # will have to test what has the best performance, when lot of
        # resources and meters are involved.
        for meter in meter_names:
            statistics = statistic_list(self._request, meter,
                                        query=query, period=period)
            meter = meter.replace(".", "_")
            if statistics:
                if stats_attr:
                    # I want to load only a specific attribute
                    setattr(resource, meter,
                            getattr(statistics[0], stats_attr, None))
                else:
                    # I want a dictionary of all statistics
                    setattr(resource, meter, statistics)
            else:
                setattr(resource, meter, None)

        return resource

    def resources(self, query=None, filter_func=None,
                  with_users_and_tenants=False):
        """ Obtaining resources with to query or filter_func.

        Obtains resources and also fetch tenants and users associated
        with those resources.

        :Parameters:
          - `query`: Query for fetching the Ceilometer Resources.
          - `filter_func`: Callable for filtering of the obtained
                           resources.
          - `with_users_and_tenants`: If true a user and a tenant object will
                                      be added to each resource object.
        """
        if with_users_and_tenants:
            ceilometer_usage_object = self
        else:
            ceilometer_usage_object = None
        resources = resource_list(self._request,
            query=query, ceilometer_usage_object=ceilometer_usage_object)
        if filter_func:
            resources = [resource for resource in resources if
                         filter_func(resource)]

        return resources

    def resources_with_statistics(self, query=None, meter_names=None,
                                  period=None, filter_func=None,
                                  stats_attr=None, additional_query=None,
                                  with_users_and_tenants=False):
        """ Obtaining resources with statistics data inside.

        :Parameters:
          - `query`: Query for fetching the Ceilometer Resources.
          - `filter_func`: Callable for filtering of the obtained
                           resources.
          - `meter_names`: List of meter names of which we want the
                           statistics.
          - `period`: In seconds. If no period is given, only one aggregate
                      statistic is returned. If given a faceted result will be
                      returned, dividend into given periods. Periods with no
                      data are ignored.
          - `stats_attr`: String representing the attribute name of the stats.
                          Eg. (avg, max, min...) If None is given, whole
                          statistic object is returned,
          - `additional_query`: Additional query for the statistics.
                                Eg. timespan, etc.
          - `with_users_and_tenants`: If true a user and a tenant object will
                                      be added to each resource object.
        """

        resources = self.resources(query, filter_func=filter_func,
            with_users_and_tenants=with_users_and_tenants)
        for resource in resources:
            # add statistics data into resource
            # TODO(lsmola) make this parallel, thread join can be below this
            # cycle. It can either create thread for each resource, or for
            # each meter. Resource will be probably better.
            self.update_with_statistics(resource, meter_names, period,
                                        stats_attr, additional_query, )
        return resources

    def resource_aggregates(self, queries=None):
        """ Obtaining resource aggregates with queries.

        Representing a resource aggregate by query is a most general way
        how to obtain a resource aggregates.

        :Parameters:
          - `queries`: Dictionary of named queries that defines a bulk of
                       resource aggregates.


        """
        resource_aggregates = []
        for identifier, query in queries.items():
            resource_aggregates.append(ResourceAggregate(query=query,
                                       ceilometer_usage=None,
                                       identifier=identifier))
        return resource_aggregates

    def resource_aggregates_with_statistics(self, queries=None,
            meter_names=None, period=None, filter_func=None, stats_attr=None,
            additional_query=None):
        """ Obtaining resource aggregates with statistics data inside.

        :Parameters:
          - `queries`: Dictionary of named queries that defines a bulk of
                       resource aggregates.
          - `meter_names`: List of meter names of which we want the
                           statistics.
          - `period`: In seconds. If no period is given, only one aggregate
                      statistic is returned. If given a faceted result will be
                      returned, dividend into given periods. Periods with no
                      data are ignored.
          - `stats_attr`: String representing the attribute name of the stats.
                          Eg. (avg, max, min...) If None is given, whole
                          statistic object is returned,
          - `additional_query`: Additional query for the statistics.
                                Eg. timespan, etc.
        """

        resource_aggregates = self.resource_aggregates(queries)
        for resource_aggregate in resource_aggregates:
            # add statistics data into resource
            # TODO(lsmola) make this parallel, thread join can be below this
            # cycle. It can either create thread for each resource, or for
            # each meter. Resource will be probably better.
            self.update_with_statistics(resource_aggregate, meter_names,
                                        period, stats_attr,
                                        additional_query)
        return resource_aggregates
