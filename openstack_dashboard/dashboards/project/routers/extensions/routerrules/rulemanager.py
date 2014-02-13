# Copyright 2013,  Big Switch Networks
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

import logging

from openstack_dashboard.api import neutron as api

LOG = logging.getLogger(__name__)


class RuleObject(dict):
    def __init__(self, rule):
        # ID is constructed from source and destination because the
        # database ID from neutron changes on every update, making a list of
        # sequential operations based on the DB ID invalid after the first one
        # occurs (e.g. deleting multiple from the table
        rule['id'] = rule['source'] + rule['destination']
        super(RuleObject, self).__init__(rule)
        # Horizon references id property for table operations
        self.id = rule['id']
        # Flatten into csv for display
        self.nexthops = ','.join(rule['nexthops'])


def routerrule_list(request, **params):
    if 'router_id' in params:
        params['device_id'] = params['router_id']
    if 'router' in request.META:
        router = request.META['router']
    else:
        router = api.router_get(request, params['device_id'])
    try:
        rules = router.router_rules
    except AttributeError:
        return (False, [])
    return (True, rules)


def remove_rules(request, rule_ids, **kwargs):
    LOG.debug("remove_rules(): param=%s", kwargs)
    router_id = kwargs['router_id']
    if 'reset_rules' in kwargs:
        newrules = [{'source': 'any', 'destination': 'any',
                     'action': 'permit'}]
    else:
        supported, currentrules = routerrule_list(request, **kwargs)
        if not supported:
            LOG.error("router rules not supported by router %s" % router_id)
            return
        newrules = []
        for oldrule in currentrules:
            if RuleObject(oldrule).id not in rule_ids:
                newrules.append(oldrule)
    body = {'router_rules': format_for_api(newrules)}
    new = api.router_update(request, router_id, **body)
    if 'router' in request.META:
        request.META['router'] = new
    return new


def add_rule(request, router_id, newrule, **kwargs):
    body = {'router_rules': []}
    kwargs['router_id'] = router_id
    supported, currentrules = routerrule_list(request, **kwargs)
    if not supported:
        LOG.error("router rules not supported by router %s" % router_id)
        return
    body['router_rules'] = format_for_api([newrule] + currentrules)
    new = api.router_update(request, router_id, **body)
    if 'router' in request.META:
        request.META['router'] = new
    return new


def format_for_api(rules):
    apiformrules = []
    for r in rules:
        # make a copy so we don't damage original dict in rules
        flattened = r.copy()
        # nexthops should only be present if there are nexthop addresses
        if 'nexthops' in flattened:
            cleanednh = [nh.strip()
                         for nh in flattened['nexthops']
                         if nh.strip()]
            if cleanednh:
                flattened['nexthops'] = '+'.join(cleanednh)
            else:
                del flattened['nexthops']
        if 'id' in flattened:
            del flattened['id']
        apiformrules.append(flattened)
    return apiformrules
