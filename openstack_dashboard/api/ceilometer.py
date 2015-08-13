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

from collections import OrderedDict
import threading

from ceilometerclient import client as ceilometer_client
from django.conf import settings
from django.utils.translation import ugettext_lazy as _

from horizon import exceptions
from horizon.utils.memoized import memoized  # noqa

from openstack_dashboard.api import base
from openstack_dashboard.api import keystone
from openstack_dashboard.api import nova


def get_flavor_names(request):
    # TODO(lsmola) The flavors can be set per project,
    # so it should show only valid ones.
    try:
        flavors = nova.flavor_list(request, None)
        return [f.name for f in flavors]
    except Exception:
        return ['m1.tiny', 'm1.small', 'm1.medium',
                'm1.large', 'm1.xlarge']


def is_iterable(var):
    """Return True if the given is list or tuple."""

    return (isinstance(var, (list, tuple)) or
            issubclass(var.__class__, (list, tuple)))


def make_query(user_id=None, tenant_id=None, resource_id=None,
               user_ids=None, tenant_ids=None, resource_ids=None):
    """Returns query built from given parameters.

    This query can be then used for querying resources, meters and
    statistics.

    :Parameters:
      - `user_id`: user_id, has a priority over list of ids
      - `tenant_id`: tenant_id, has a priority over list of ids
      - `resource_id`: resource_id, has a priority over list of ids
      - `user_ids`: list of user_ids
      - `tenant_ids`: list of tenant_ids
      - `resource_ids`: list of resource_ids
    """
    user_ids = user_ids or []
    tenant_ids = tenant_ids or []
    resource_ids = resource_ids or []

    query = []
    if user_id:
        user_ids = [user_id]
    for u_id in user_ids:
        query.append({"field": "user_id", "op": "eq", "value": u_id})

    if tenant_id:
        tenant_ids = [tenant_id]
    for t_id in tenant_ids:
        query.append({"field": "project_id", "op": "eq", "value": t_id})

    if resource_id:
        resource_ids = [resource_id]
    for r_id in resource_ids:
        query.append({"field": "resource_id", "op": "eq", "value": r_id})

    return query


class Meter(base.APIResourceWrapper):
    """Represents one Ceilometer meter."""
    _attrs = ['name', 'type', 'unit', 'resource_id', 'user_id', 'project_id']

    def __init__(self, apiresource):
        super(Meter, self).__init__(apiresource)

        self._label = self.name
        self._description = ""

    def augment(self, label=None, description=None):
        if label:
            self._label = label
        if description:
            self._description = description

    @property
    def description(self):
        return self._description

    @property
    def label(self):
        return self._label


class Resource(base.APIResourceWrapper):
    """Represents one Ceilometer resource."""
    _attrs = ['resource_id', 'source', 'user_id', 'project_id', 'metadata',
              'links']

    def __init__(self, apiresource, ceilometer_usage=None):
        super(Resource, self).__init__(apiresource)

        # Save empty strings to IDs rather than None, so it gets
        # serialized correctly. We don't want 'None' strings.
        self.project_id = self.project_id or ""
        self.user_id = self.user_id or ""
        self.resource_id = self.resource_id or ""

        self._id = "%s__%s__%s" % (self.project_id,
                                   self.user_id,
                                   self.resource_id)

        # Meters with statistics data
        self._meters = {}

        # TODO(lsmola) make parallel obtaining of tenant and user
        # make the threading here, thread join into resource_list
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

    @property
    def meters(self):
        return self._meters

    def get_meter(self, meter_name):
        return self._meters.get(meter_name, None)

    def set_meter(self, meter_name, value):
        self._meters[meter_name] = value


class ResourceAggregate(Resource):
    """Represents aggregate of more resources together.

    Aggregate of resources can be obtained by specifying
    multiple ids in one parameter or by not specifying
    one parameter.
    It can also be specified by query directly.

    Example:
        We can obtain an aggregate of resources by specifying
        multiple resource_ids in resource_id parameter in init.
        Or we can specify only tenant_id, which will return
        all resources of that tenant.
    """

    def __init__(self, tenant_id=None, user_id=None, resource_id=None,
                 tenant_ids=None, user_ids=None, resource_ids=None,
                 ceilometer_usage=None, query=None, identifier=None):

        self._id = identifier

        self.tenant_id = None
        self.user_id = None
        self.resource_id = None

        # Meters with statistics data
        self._meters = {}

        if query:
            self._query = query
        else:
            # TODO(lsmola) make parallel obtaining of tenant and user
            # make the threading here, thread join into resource_list
            if ceilometer_usage and tenant_id:
                self.tenant_id = tenant_id
                self._tenant = ceilometer_usage.get_tenant(tenant_id)
            else:
                self._tenant = None

            if ceilometer_usage and user_id:
                self.user_id = user_id
                self._user = ceilometer_usage.get_user(user_id)
            else:
                self._user = None

            if resource_id:
                self.resource_id = resource_id

            self._query = make_query(tenant_id=tenant_id, user_id=user_id,
                                     resource_id=resource_id,
                                     tenant_ids=tenant_ids,
                                     user_ids=user_ids,
                                     resource_ids=resource_ids)

    @property
    def id(self):
        return self._id


class Sample(base.APIResourceWrapper):
    """Represents one Ceilometer sample."""

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
    """Represents one Ceilometer statistic."""

    _attrs = ['period', 'period_start', 'period_end',
              'count', 'min', 'max', 'sum', 'avg',
              'duration', 'duration_start', 'duration_end']


class Alarm(base.APIResourceWrapper):
    """Represents one Ceilometer alarm."""
    _attrs = ['alarm_actions', 'ok_actions', 'name',
              'timestamp', 'description', 'time_constraints',
              'enabled', 'state_timestamp', 'alarm_id',
              'state', 'insufficient_data_actions',
              'repeat_actions', 'user_id', 'project_id',
              'type', 'severity', 'threshold_rule', 'period', 'query',
              'evaluation_periods', 'statistic', 'meter_name',
              'threshold', 'comparison_operator', 'exclude_outliers']

    def __init__(self, apiresource, ceilometer_usage=None):
        super(Alarm, self).__init__(apiresource)
        self._tenant = None
        self._user = None

        if ceilometer_usage and self.project_id:
            self._tenant = ceilometer_usage.get_tenant(self.project_id)

        if ceilometer_usage and self.user_id:
            self._user = ceilometer_usage.get_user(self.user_id)

    @property
    def id(self):
        return self.alarm_id

    @property
    def tenant(self):
        return self._tenant

    @property
    def user(self):
        return self._user


@memoized
def ceilometerclient(request):
    """Initialization of Ceilometer client."""

    endpoint = base.url_for(request, 'metering')
    insecure = getattr(settings, 'OPENSTACK_SSL_NO_VERIFY', False)
    cacert = getattr(settings, 'OPENSTACK_SSL_CACERT', None)
    return ceilometer_client.Client('2', endpoint,
                                    token=(lambda: request.user.token.id),
                                    insecure=insecure,
                                    cacert=cacert)


def alarm_list(request, query=None, ceilometer_usage=None):
    """List alarms."""
    alarms = ceilometerclient(request).alarms.list(q=query)
    return [Alarm(alarm, ceilometer_usage) for alarm in alarms]


def alarm_get(request, alarm_id, ceilometer_usage=None):
    """Get an alarm."""
    alarm = ceilometerclient(request).alarms.get(alarm_id)
    return Alarm(alarm, ceilometer_usage)


def alarm_update(request, alarm_id, ceilometer_usage=None, **kwargs):
    """Update an alarm."""
    alarm = ceilometerclient(request).alarms.update(alarm_id, **kwargs)
    return Alarm(alarm, ceilometer_usage)


def alarm_delete(request, alarm_id):
    """Delete an alarm."""
    ceilometerclient(request).alarms.delete(alarm_id)


def alarm_create(request, ceilometer_usage=None, **kwargs):
    """Create an alarm."""
    alarm = ceilometerclient(request).alarms.create(**kwargs)
    return Alarm(alarm, ceilometer_usage)


def resource_list(request, query=None, ceilometer_usage_object=None):
    """List the resources."""
    resources = ceilometerclient(request).resources.list(q=query)
    return [Resource(r, ceilometer_usage_object) for r in resources]


def sample_list(request, meter_name, query=None, limit=None):
    """List the samples for this meters."""
    samples = ceilometerclient(request).samples.list(meter_name=meter_name,
                                                     q=query, limit=limit)
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


class ThreadedUpdateResourceWithStatistics(threading.Thread):
    """Multithread wrapper for update_with_statistics method of
    resource_usage.

    A join logic is placed in process_list class method. All resources
    will have its statistics attribute filled in separate threads.

    The resource_usage object is shared between threads. Each thread is
    updating one Resource.

    :Parameters:
      - `resource`: Resource or ResourceAggregate object, that will
                    be filled by statistic data.
      - `resources`: List of Resource or ResourceAggregate object,
                     that will be filled by statistic data.
      - `resource_usage`: Wrapping resource usage object, that holds
                          all statistics data.
      - `meter_names`: List of meter names of the statistics we want.
      - `period`: In seconds. If no period is given, only one aggregate
                  statistic is returned. If given, a faceted result will be
                  returned, divided into given periods. Periods with no
                  data are ignored.
      - `stats_attr`: String representing the attribute name of the stats.
                      E.g. (avg, max, min...) If None is given, whole
                      statistic object is returned,
      - `additional_query`: Additional query for the statistics.
                            E.g. timespan, etc.
    """
    # TODO(lsmola) Can be removed once Ceilometer supports sample-api
    # and group-by, so all of this optimization will not be necessary.
    # It is planned somewhere to I.

    def __init__(self, resource_usage, resource, meter_names=None,
                 period=None, filter_func=None, stats_attr=None,
                 additional_query=None):
        super(ThreadedUpdateResourceWithStatistics, self).__init__()
        self.resource_usage = resource_usage
        self.resource = resource
        self.meter_names = meter_names
        self.period = period
        self.stats_attr = stats_attr
        self.additional_query = additional_query

    def run(self):
        # Run the job
        self.resource_usage.update_with_statistics(
            self.resource,
            meter_names=self.meter_names, period=self.period,
            stats_attr=self.stats_attr, additional_query=self.additional_query)

    @classmethod
    def process_list(cls, resource_usage, resources, meter_names=None,
                     period=None, filter_func=None, stats_attr=None,
                     additional_query=None):
        threads = []

        for resource in resources:
            # add statistics data into resource
            thread = cls(resource_usage, resource, meter_names=meter_names,
                         period=period, stats_attr=stats_attr,
                         additional_query=additional_query)
            thread.start()
            threads.append(thread)

        for thread in threads:
            thread.join()


class CeilometerUsage(object):
    """Represents wrapper of any Ceilometer queries.

    One instance of this class should be shared between resources
    as this class provides a place where users and tenants are
    cached. So there are no duplicate queries to API.

    This class also wraps Ceilometer API calls and provides parallel
    HTTP calls to API.

    This class should also serve as reasonable abstraction, that will
    cover huge amount of optimization due to optimization of Ceilometer
    service, without changing of the interface.
    """

    def __init__(self, request):
        self._request = request

        # Cached users and tenants.
        self._users = {}
        self._tenants = {}

    def get_user(self, user_id):
        """Returns user fetched from API.

        Caching the result, so it doesn't contact API twice with the
        same query.
        """

        user = self._users.get(user_id, None)
        if not user:
            user = keystone.user_get(self._request, user_id)
            # caching the user, for later use
            self._users[user_id] = user
        return user

    def preload_all_users(self):
        """Preloads all users into dictionary.

        It's more effective to preload all users, rather than fetching many
        users by separate API get calls.
        """

        users = keystone.user_list(self._request)
        # Cache all users on right indexes, this is more effective than to
        # obtain large number of users one by one by keystone.user_get
        for u in users:
            self._users[u.id] = u

    def get_tenant(self, tenant_id):
        """Returns tenant fetched from API.

        Caching the result, so it doesn't contact API twice with the
        same query.
        """

        tenant = self._tenants.get(tenant_id, None)
        if not tenant:
            tenant = keystone.tenant_get(self._request, tenant_id)
            # caching the tenant for later use
            self._tenants[tenant_id] = tenant
        return tenant

    def preload_all_tenants(self):
        """Preloads all tenants into dictionary.

        It's more effective to preload all tenants, rather than fetching each
        tenant by separate API get calls.
        """

        tenants, more = keystone.tenant_list(self._request)
        # Cache all tenants on right indexes, this is more effective than to
        # obtain large number of tenants one by one by keystone.tenant_get
        for t in tenants:
            self._tenants[t.id] = t

    def global_data_get(self, used_cls=None, query=None,
                        with_statistics=False, additional_query=None,
                        with_users_and_tenants=True):
        """Obtaining a resources for table view.

        It obtains resources with statistics data according to declaration
        in used_cls class.

        :Parameters:
          - `user_cls`: Class wrapper for usage data. It acts as wrapper for
                        settings needed. See the call of this method for
                        details.
          - `query`: Explicit query definition for fetching the resources. If
                     no query is provided, it takes a default_query from
                     used_cls. If no default query is provided, it fetches
                     all the resources and filters them by meters defined
                     in used_cls.
          - `with_statistic`: Define whether statistics data from the meters
                              defined in used_cls should be fetched.
                              Can be used to first obtain only the pure
                              resources, then with the statistics data by
                              AJAX.
          - `additional_query`: Additional query for the statistics.
                                E.g. timespan, etc.
          - `with_users_and_tenants`: If true a user and a tenant object will
                                      be added to each resource object.
        """

        default_query = used_cls.default_query
        query = query or default_query
        filter_func = None

        def filter_resources(resource):
            """Method for filtering resources by their links.rel attr.

            The links.rel attributes contain all meters the resource has.
            """
            for link in resource.links:
                if link['rel'] in used_cls.meters:
                    return True
            return False

        if not query:
            # Not all resource types can be obtained by query, if there is not
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
            resources = self.resources(
                query, filter_func=filter_func,
                with_users_and_tenants=with_users_and_tenants)

        return [used_cls(resource) for resource in resources]

    def query_from_object_id(self, object_id):
        """Obtaining a query from resource id.

        Query can be then used to identify a resource in resources or meters
        API calls. ID is being built in the Resource initializer, or returned
        by Datatable into UpdateRow functionality.
        """
        try:
            tenant_id, user_id, resource_id = object_id.split("__")
        except ValueError:
            return []

        return make_query(tenant_id=tenant_id, user_id=user_id,
                          resource_id=resource_id)

    def update_with_statistics(self, resource, meter_names=None, period=None,
                               stats_attr=None, additional_query=None):
        """Adding statistical data into one Resource or ResourceAggregate.

        It adds each statistic of each meter_names into the resource
        attributes. Attribute name is the meter name with replaced '.' to '_'.

        :Parameters:
          - `resource`: Resource or ResourceAggregate object, that will
                        be filled by statistic data.
          - `meter_names`: List of meter names of which we want the
                           statistics.
          - `period`: In seconds. If no period is given, only one aggregate
                      statistic is returned. If given a faceted result will be
                      returned, dividend into given periods. Periods with no
                      data are ignored.
          - `stats_attr`: String representing the specific name of the stats.
                          E.g. (avg, max, min...) If defined, meter attribute
                          will contain just the one value. If None is given,
                          meter attribute will contain the whole Statistic
                          object.
          - `additional_query`: Additional query for the statistics.
                                E.g. timespan, etc.
        """

        if not meter_names:
            raise ValueError("meter_names and resources must be defined to be "
                             "able to obtain the statistics.")

        # query for identifying one resource in meters
        query = resource.query
        if additional_query:
            if not is_iterable(additional_query):
                raise ValueError("Additional query must be list of"
                                 " conditions. See the docs for format.")
            query = query + additional_query

        # TODO(lsmola) thread for each meter will be probably overkill
        # but I should test lets say thread pool with 100 of threads
        # and apply it only to this code.
        # Though I do expect Ceilometer will support bulk requests,
        # so all of this optimization will not be necessary.
        for meter in meter_names:
            statistics = statistic_list(self._request, meter,
                                        query=query, period=period)
            meter = meter.replace(".", "_")
            if statistics:
                if stats_attr:
                    # I want to load only a specific attribute
                    resource.set_meter(
                        meter,
                        getattr(statistics[0], stats_attr, None))
                else:
                    # I want a dictionary of all statistics
                    resource.set_meter(meter, statistics)
            else:
                resource.set_meter(meter, None)

        return resource

    def resources(self, query=None, filter_func=None,
                  with_users_and_tenants=False):
        """Obtaining resources with the query or filter_func.

        Obtains resources and also fetch tenants and users associated
        with those resources if with_users_and_tenants flag is true.

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
        resources = resource_list(
            self._request,
            query=query, ceilometer_usage_object=ceilometer_usage_object)
        if filter_func:
            resources = [resource for resource in resources if
                         filter_func(resource)]

        return resources

    def resources_with_statistics(self, query=None, meter_names=None,
                                  period=None, filter_func=None,
                                  stats_attr=None, additional_query=None,
                                  with_users_and_tenants=False):
        """Obtaining resources with statistics data inside.

        :Parameters:
          - `query`: Query for fetching the Ceilometer Resources.
          - `filter_func`: Callable for filtering of the obtained
                           resources.
          - `meter_names`: List of meter names of which we want the
                           statistics.
          - `period`: In seconds. If no period is given, only one aggregate
                      statistic is returned. If given, a faceted result will
                      be returned, divided into given periods. Periods with
                      no data are ignored.
          - `stats_attr`: String representing the specific name of the stats.
                          E.g. (avg, max, min...) If defined, meter attribute
                          will contain just the one value. If None is given,
                          meter attribute will contain the whole Statistic
                          object.
          - `additional_query`: Additional query for the statistics.
                                E.g. timespan, etc.
          - `with_users_and_tenants`: If true a user and a tenant object will
                                      be added to each resource object.
        """

        resources = self.resources(
            query, filter_func=filter_func,
            with_users_and_tenants=with_users_and_tenants)

        ThreadedUpdateResourceWithStatistics.process_list(
            self, resources,
            meter_names=meter_names, period=period, stats_attr=stats_attr,
            additional_query=additional_query)

        return resources

    def resource_aggregates(self, queries=None):
        """Obtaining resource aggregates with queries.

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
                                            meter_names=None, period=None,
                                            filter_func=None, stats_attr=None,
                                            additional_query=None):
        """Obtaining resource aggregates with statistics data inside.

        :Parameters:
          - `queries`: Dictionary of named queries that defines a bulk of
                       resource aggregates.
          - `meter_names`: List of meter names of which we want the
                           statistics.
          - `period`: In seconds. If no period is given, only one aggregate
                      statistic is returned. If given, a faceted result will
                      be returned, divided into given periods. Periods with
                      no data are ignored.
          - `stats_attr`: String representing the specific name of the stats.
                          E.g. (avg, max, min...) If defined, meter attribute
                          will contain just the one value. If None is given,
                          meter attribute will contain the whole Statistic
                          object.
          - `additional_query`: Additional query for the statistics.
                                E.g. timespan, etc.
        """
        resource_aggregates = self.resource_aggregates(queries)

        ThreadedUpdateResourceWithStatistics.process_list(
            self,
            resource_aggregates, meter_names=meter_names, period=period,
            stats_attr=stats_attr, additional_query=additional_query)

        return resource_aggregates


def diff_lists(a, b):
    if not a:
        return []
    elif not b:
        return a
    else:
        return list(set(a) - set(b))


class Meters(object):
    """Class for listing of available meters.

    It is listing meters defined in this class that are available
    in Ceilometer meter_list.

    It is storing information that is not available in Ceilometer, i.e.
    label, description.

    """

    def __init__(self, request=None, ceilometer_meter_list=None):
        # Storing the request.
        self._request = request

        # Storing the Ceilometer meter list
        if ceilometer_meter_list:
            self._ceilometer_meter_list = ceilometer_meter_list
        else:
            try:
                self._ceilometer_meter_list = meter_list(request)
            except Exception:
                self._ceilometer_meter_list = []
                exceptions.handle(self._request,
                                  _('Unable to retrieve Ceilometer meter '
                                    'list.'))

        # Storing the meters info categorized by their services.
        self._nova_meters_info = self._get_nova_meters_info()
        self._neutron_meters_info = self._get_neutron_meters_info()
        self._glance_meters_info = self._get_glance_meters_info()
        self._cinder_meters_info = self._get_cinder_meters_info()
        self._swift_meters_info = self._get_swift_meters_info()
        self._kwapi_meters_info = self._get_kwapi_meters_info()
        self._ipmi_meters_info = self._get_ipmi_meters_info()

        # Storing the meters info of all services together.
        all_services_meters = (self._nova_meters_info,
                               self._neutron_meters_info,
                               self._glance_meters_info,
                               self._cinder_meters_info,
                               self._swift_meters_info,
                               self._kwapi_meters_info,
                               self._ipmi_meters_info)
        self._all_meters_info = {}
        for service_meters in all_services_meters:
            self._all_meters_info.update(dict([(meter_name, meter_info)
                                               for meter_name, meter_info
                                               in service_meters.items()]))

        # Here will be the cached Meter objects, that will be reused for
        # repeated listing.
        self._cached_meters = {}

    def list_all(self, only_meters=None, except_meters=None):
        """Returns a list of meters based on the meters names.

        :Parameters:
          - `only_meters`: The list of meter names we want to show.
          - `except_meters`: The list of meter names we don't want to show.
        """

        return self._list(only_meters=only_meters,
                          except_meters=except_meters)

    def list_nova(self, except_meters=None):
        """Returns a list of meters tied to nova.

        :Parameters:
          - `except_meters`: The list of meter names we don't want to show.
        """

        return self._list(only_meters=self._nova_meters_info.keys(),
                          except_meters=except_meters)

    def list_neutron(self, except_meters=None):
        """Returns a list of meters tied to neutron.

        :Parameters:
          - `except_meters`: The list of meter names we don't want to show.
        """

        return self._list(only_meters=self._neutron_meters_info.keys(),
                          except_meters=except_meters)

    def list_glance(self, except_meters=None):
        """Returns a list of meters tied to glance.

        :Parameters:
          - `except_meters`: The list of meter names we don't want to show.
        """

        return self._list(only_meters=self._glance_meters_info.keys(),
                          except_meters=except_meters)

    def list_cinder(self, except_meters=None):
        """Returns a list of meters tied to cinder.

        :Parameters:
          - `except_meters`: The list of meter names we don't want to show.
        """

        return self._list(only_meters=self._cinder_meters_info.keys(),
                          except_meters=except_meters)

    def list_swift(self, except_meters=None):
        """Returns a list of meters tied to swift.

        :Parameters:
          - `except_meters`: The list of meter names we don't want to show.
        """

        return self._list(only_meters=self._swift_meters_info.keys(),
                          except_meters=except_meters)

    def list_kwapi(self, except_meters=None):
        """Returns a list of meters tied to kwapi.

        :Parameters:
          - `except_meters`: The list of meter names we don't want to show.
        """

        return self._list(only_meters=self._kwapi_meters_info.keys(),
                          except_meters=except_meters)

    def list_ipmi(self, except_meters=None):
        """Returns a list of meters tied to ipmi

        :Parameters:
          - `except_meters`: The list of meter names we don't want to show
        """

        return self._list(only_meters=self._ipmi_meters_info.keys(),
                          except_meters=except_meters)

    def _list(self, only_meters=None, except_meters=None):
        """Returns a list of meters based on the meters names.

        :Parameters:
          - `only_meters`: The list of meter names we want to show.
          - `except_meters`: The list of meter names we don't want to show.
        """

        # Get all wanted meter names.
        if only_meters:
            meter_names = only_meters
        else:
            meter_names = [meter_name for meter_name
                           in self._all_meters_info.keys()]

        meter_names = diff_lists(meter_names, except_meters)
        # Collect meters for wanted meter names.
        return self._get_meters(meter_names)

    def _get_meters(self, meter_names):
        """Obtain meters based on meter_names.

        The meters that do not exist in Ceilometer meter list are left out.

        :Parameters:
          - `meter_names`: A list of meter names we want to fetch.
        """

        meters = []
        for meter_name in meter_names:
            meter = self._get_meter(meter_name)
            if meter:
                meters.append(meter)
        return meters

    def _get_meter(self, meter_name):
        """Obtains a meter.

        Obtains meter either from cache or from Ceilometer meter list
        joined with statically defined meter info like label and description.

        :Parameters:
          - `meter_name`: A meter name we want to fetch.
        """
        meter = self._cached_meters.get(meter_name, None)
        if not meter:
            meter_candidates = [m for m in self._ceilometer_meter_list
                                if m.name == meter_name]

            if meter_candidates:
                meter_info = self._all_meters_info.get(meter_name, None)
                if meter_info:
                    label = meter_info["label"]
                    description = meter_info["description"]
                else:
                    label = ""
                    description = ""
                meter = meter_candidates[0]
                meter.augment(label=label, description=description)

                self._cached_meters[meter_name] = meter

        return meter

    def _get_nova_meters_info(self):
        """Returns additional info for each meter.

        That will be used for augmenting the Ceilometer meter.
        """

        # TODO(lsmola) Unless the Ceilometer will provide the information
        # below, I need to define it as a static here. I will be joining this
        # to info that I am able to obtain from Ceilometer meters, hopefully
        # some day it will be supported all.
        meters_info = OrderedDict([
            ("instance", {
                'label': '',
                'description': _("Existence of instance"),
            }),
            ("instance:<type>", {
                'label': '',
                'description': _("Existence of instance <type> "
                                 "(openstack types)"),
            }),
            ("memory", {
                'label': '',
                'description': _("Volume of RAM"),
            }),
            ("memory.usage", {
                'label': '',
                'description': _("Volume of RAM used"),
            }),
            ("cpu", {
                'label': '',
                'description': _("CPU time used"),
            }),
            ("cpu_util", {
                'label': '',
                'description': _("Average CPU utilization"),
            }),
            ("vcpus", {
                'label': '',
                'description': _("Number of VCPUs"),
            }),
            ("disk.read.requests", {
                'label': '',
                'description': _("Number of read requests"),
            }),
            ("disk.write.requests", {
                'label': '',
                'description': _("Number of write requests"),
            }),
            ("disk.read.bytes", {
                'label': '',
                'description': _("Volume of reads"),
            }),
            ("disk.write.bytes", {
                'label': '',
                'description': _("Volume of writes"),
            }),
            ("disk.read.requests.rate", {
                'label': '',
                'description': _("Average rate of read requests"),
            }),
            ("disk.write.requests.rate", {
                'label': '',
                'description': _("Average rate of write requests"),
            }),
            ("disk.read.bytes.rate", {
                'label': '',
                'description': _("Average rate of reads"),
            }),
            ("disk.write.bytes.rate", {
                'label': '',
                'description': _("Average volume of writes"),
            }),
            ("disk.root.size", {
                'label': '',
                'description': _("Size of root disk"),
            }),
            ("disk.ephemeral.size", {
                'label': '',
                'description': _("Size of ephemeral disk"),
            }),
            ("network.incoming.bytes", {
                'label': '',
                'description': _("Number of incoming bytes "
                                 "on the network for a VM interface"),
            }),
            ("network.outgoing.bytes", {
                'label': '',
                'description': _("Number of outgoing bytes "
                                 "on the network for a VM interface"),
            }),
            ("network.incoming.packets", {
                'label': '',
                'description': _("Number of incoming "
                                 "packets for a VM interface"),
            }),
            ("network.outgoing.packets", {
                'label': '',
                'description': _("Number of outgoing "
                                 "packets for a VM interface"),
            }),
            ("network.incoming.bytes.rate", {
                'label': '',
                'description': _("Average rate per sec of incoming "
                                 "bytes on a VM network interface"),
            }),
            ("network.outgoing.bytes.rate", {
                'label': '',
                'description': _("Average rate per sec of outgoing "
                                 "bytes on a VM network interface"),
            }),
            ("network.incoming.packets.rate", {
                'label': '',
                'description': _("Average rate per sec of incoming "
                                 "packets on a VM network interface"),
            }),
            ("network.outgoing.packets.rate", {
                'label': '',
                'description': _("Average rate per sec of outgoing "
                                 "packets on a VM network interface"),
            }),
        ])
        # Adding flavor based meters into meters_info dict
        # TODO(lsmola) this kind of meter will be probably deprecated
        # https://bugs.launchpad.net/ceilometer/+bug/1208365 . Delete it then.
        for flavor in get_flavor_names(self._request):
            name = 'instance:%s' % flavor
            meters_info[name] = dict(meters_info["instance:<type>"])

            meters_info[name]['description'] = (
                _('Duration of instance type %s (openstack flavor)') %
                flavor)

        # TODO(lsmola) allow to set specific in local_settings. For all meters
        # because users can have their own agents and meters.
        return meters_info

    def _get_neutron_meters_info(self):
        """Returns additional info for each meter.

        That will be used for augmenting the Ceilometer meter.
        """

        # TODO(lsmola) Unless the Ceilometer will provide the information
        # below, I need to define it as a static here. I will be joining this
        # to info that I am able to obtain from Ceilometer meters, hopefully
        # some day it will be supported all.
        return OrderedDict([
            ('network', {
                'label': '',
                'description': _("Existence of network"),
            }),
            ('network.create', {
                'label': '',
                'description': _("Creation requests for this network"),
            }),
            ('network.update', {
                'label': '',
                'description': _("Update requests for this network"),
            }),
            ('subnet', {
                'label': '',
                'description': _("Existence of subnet"),
            }),
            ('subnet.create', {
                'label': '',
                'description': _("Creation requests for this subnet"),
            }),
            ('subnet.update', {
                'label': '',
                'description': _("Update requests for this subnet"),
            }),
            ('port', {
                'label': '',
                'description': _("Existence of port"),
            }),
            ('port.create', {
                'label': '',
                'description': _("Creation requests for this port"),
            }),
            ('port.update', {
                'label': '',
                'description': _("Update requests for this port"),
            }),
            ('router', {
                'label': '',
                'description': _("Existence of router"),
            }),
            ('router.create', {
                'label': '',
                'description': _("Creation requests for this router"),
            }),
            ('router.update', {
                'label': '',
                'description': _("Update requests for this router"),
            }),
            ('ip.floating', {
                'label': '',
                'description': _("Existence of floating ip"),
            }),
            ('ip.floating.create', {
                'label': '',
                'description': _("Creation requests for this floating ip"),
            }),
            ('ip.floating.update', {
                'label': '',
                'description': _("Update requests for this floating ip"),
            }),
        ])

    def _get_glance_meters_info(self):
        """Returns additional info for each meter.

        That will be used for augmenting the Ceilometer meter.
        """

        # TODO(lsmola) Unless the Ceilometer will provide the information
        # below, I need to define it as a static here. I will be joining this
        # to info that I am able to obtain from Ceilometer meters, hopefully
        # some day it will be supported all.
        return OrderedDict([
            ('image', {
                'label': '',
                'description': _("Image existence check"),
            }),
            ('image.size', {
                'label': '',
                'description': _("Uploaded image size"),
            }),
            ('image.update', {
                'label': '',
                'description': _("Number of image updates"),
            }),
            ('image.upload', {
                'label': '',
                'description': _("Number of image uploads"),
            }),
            ('image.delete', {
                'label': '',
                'description': _("Number of image deletions"),
            }),
            ('image.download', {
                'label': '',
                'description': _("Image is downloaded"),
            }),
            ('image.serve', {
                'label': '',
                'description': _("Image is served out"),
            }),
        ])

    def _get_cinder_meters_info(self):
        """Returns additional info for each meter.

        That will be used for augmenting the Ceilometer meter.
        """

        # TODO(lsmola) Unless the Ceilometer will provide the information
        # below, I need to define it as a static here. I will be joining this
        # to info that I am able to obtain from Ceilometer meters, hopefully
        # some day it will be supported all.
        return OrderedDict([
            ('volume', {
                'label': '',
                'description': _("Existence of volume"),
            }),
            ('volume.size', {
                'label': '',
                'description': _("Size of volume"),
            }),
        ])

    def _get_swift_meters_info(self):
        """Returns additional info for each meter.

        That will be used for augmenting the Ceilometer meter.
        """

        # TODO(lsmola) Unless the Ceilometer will provide the information
        # below, I need to define it as a static here. I will be joining this
        # to info that I am able to obtain from Ceilometer meters, hopefully
        # some day it will be supported all.
        return OrderedDict([
            ('storage.objects', {
                'label': '',
                'description': _("Number of objects"),
            }),
            ('storage.objects.size', {
                'label': '',
                'description': _("Total size of stored objects"),
            }),
            ('storage.objects.containers', {
                'label': '',
                'description': _("Number of containers"),
            }),
            ('storage.objects.incoming.bytes', {
                'label': '',
                'description': _("Number of incoming bytes"),
            }),
            ('storage.objects.outgoing.bytes', {
                'label': '',
                'description': _("Number of outgoing bytes"),
            }),
            ('storage.api.request', {
                'label': '',
                'description': _("Number of API requests against swift"),
            }),
        ])

    def _get_kwapi_meters_info(self):
        """Returns additional info for each meter.

        That will be used for augmenting the Ceilometer meter.
        """

        # TODO(lsmola) Unless the Ceilometer will provide the information
        # below, I need to define it as a static here. I will be joining this
        # to info that I am able to obtain from Ceilometer meters, hopefully
        # some day it will be supported all.
        return OrderedDict([
            ('energy', {
                'label': '',
                'description': _("Amount of energy"),
            }),
            ('power', {
                'label': '',
                'description': _("Power consumption"),
            }),
        ])

    def _get_ipmi_meters_info(self):
        """Returns additional info for each meter

        That will be used for augmenting the Ceilometer meter
        """

        # TODO(lsmola) Unless the Ceilometer will provide the information
        # below, I need to define it as a static here. I will be joining this
        # to info that I am able to obtain from Ceilometer meters, hopefully
        # some day it will be supported all.
        return OrderedDict([
            ('hardware.ipmi.node.power', {
                'label': '',
                'description': _("System Current Power"),
            }),
            ('hardware.ipmi.fan', {
                'label': '',
                'description': _("Fan RPM"),
            }),
            ('hardware.ipmi.temperature', {
                'label': '',
                'description': _("Sensor Temperature Reading"),
            }),
            ('hardware.ipmi.current', {
                'label': '',
                'description': _("Sensor Current Reading"),
            }),
            ('hardware.ipmi.voltage', {
                'label': '',
                'description': _("Sensor Voltage Reading"),
            }),
            ('hardware.ipmi.node.temperature', {
                'label': '',
                'description': _("System Temperature Reading"),
            }),
            ('hardware.ipmi.node.outlet_temperature', {
                'label': '',
                'description': _("System Outlet Temperature Reading"),
            }),
            ('hardware.ipmi.node.airflow', {
                'label': '',
                'description': _("System Airflow Reading"),
            }),
            ('hardware.ipmi.node.cups', {
                'label': '',
                'description': _("System CUPS Reading"),
            }),
            ('hardware.ipmi.node.cpu_util', {
                'label': '',
                'description': _("System CPU Utility Reading"),
            }),
            ('hardware.ipmi.node.mem_util', {
                'label': '',
                'description': _("System Memory Utility Reading"),
            }),
            ('hardware.ipmi.node.io_util', {
                'label': '',
                'description': _("System IO Utility Reading"),
            }),
        ])
