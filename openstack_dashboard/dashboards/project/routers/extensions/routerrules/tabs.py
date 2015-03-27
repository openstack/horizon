# Copyright 2013
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

import netaddr

from django import template
from django.template.loader import render_to_string
from django.utils.translation import ugettext_lazy as _

from horizon import tabs

from openstack_dashboard import api
from openstack_dashboard.dashboards.project.routers.extensions.routerrules\
    import rulemanager
from openstack_dashboard.dashboards.project.routers.extensions.routerrules\
    import tables as rrtbl


class RouterRulesTab(tabs.TableTab):
    table_classes = (rrtbl.RouterRulesTable,)
    name = _("Router Rules")
    slug = "routerrules"
    template_name = "horizon/common/_detail_table.html"

    def allowed(self, request):
        try:
            getattr(self.tab_group.kwargs['router'], 'router_rules')
            return True
        except Exception:
            return False

    def get_routerrules_data(self):
        try:
            routerrules = getattr(self.tab_group.kwargs['router'],
                                  'router_rules')
        except Exception:
            routerrules = []
        return [rulemanager.RuleObject(r) for r in routerrules]

    def post(self, request, *args, **kwargs):
        if request.POST['action'] == 'routerrules__resetrules':
            kwargs['reset_rules'] = True
            rulemanager.remove_rules(request, [], **kwargs)
            self.tab_group.kwargs['router'] = \
                api.neutron.router_get(request, kwargs['router_id'])


class RulesGridTab(tabs.Tab):
    name = _("Router Rules Grid")
    slug = "rulesgrid"
    template_name = ("project/routers/extensions/routerrules/grid.html")

    def allowed(self, request):
        try:
            getattr(self.tab_group.kwargs['router'], 'router_rules')
            return True
        except Exception:
            return False

    def render(self):
        context = template.RequestContext(self.request)
        return render_to_string(self.get_template_name(self.request),
                                self.data, context_instance=context)

    def get_context_data(self, request, **kwargs):
        data = {'router': {'id':
                           self.tab_group.kwargs['router_id']}}
        self.request = request
        rules, supported = self.get_routerrules_data(checksupport=True)
        if supported:
            data["rulesmatrix"] = self.get_routerrulesgrid_data(rules)
        return data

    def get_routerrulesgrid_data(self, rules):
        ports = self.tab_group.kwargs['ports']
        networks = api.neutron.network_list_for_tenant(
            self.request, self.request.user.tenant_id)
        netnamemap = {}
        subnetmap = {}
        for n in networks:
            netnamemap[n['id']] = n.name_or_id
            for s in n.subnets:
                subnetmap[s.id] = {'name': s.name,
                                   'cidr': s.cidr}

        matrix = []
        subnets = []
        for port in ports:
            for ip in port['fixed_ips']:
                if ip['subnet_id'] not in subnetmap:
                    continue
                sub = {'ip': ip['ip_address'],
                       'subnetid': ip['subnet_id'],
                       'subnetname': subnetmap[ip['subnet_id']]['name'],
                       'networkid': port['network_id'],
                       'networkname': netnamemap[port['network_id']],
                       'cidr': subnetmap[ip['subnet_id']]['cidr']}
                subnets.append(sub)
        subnets.append({'ip': '0.0.0.0',
                        'subnetid': 'external',
                        'subnetname': '',
                        'networkname': 'external',
                        'networkid': 'external',
                        'cidr': '0.0.0.0/0'})
        subnets.append({'ip': '0.0.0.0',
                        'subnetid': 'any',
                        'subnetname': '',
                        'networkname': 'any',
                        'networkid': 'any',
                        'cidr': '0.0.0.0/0'})
        for source in subnets:
            row = {'source': dict(source),
                   'targets': []}
            for target in subnets:
                target.update(self._get_subnet_connectivity(
                              source, target, rules))
                row['targets'].append(dict(target))
            matrix.append(row)
        return matrix

    def _get_subnet_connectivity(self, src_sub, dst_sub, rules):
        v4_any_words = ['external', 'any']
        connectivity = {'reachable': '',
                        'inverse_rule': {},
                        'rule_to_delete': False}
        src = src_sub['cidr']
        dst = dst_sub['cidr']
        # differentiate between external and any
        src_rulename = src_sub['subnetid'] if src == '0.0.0.0/0' else src
        dst_rulename = dst_sub['subnetid'] if dst == '0.0.0.0/0' else dst
        if str(src) == str(dst):
            connectivity['reachable'] = 'full'
            return connectivity
        matchingrules = []

        for rule in rules:
            rd = rule['destination']
            if rule['destination'] in v4_any_words:
                rd = '0.0.0.0/0'
            rs = rule['source']
            if rule['source'] in v4_any_words:
                rs = '0.0.0.0/0'
            rs = netaddr.IPNetwork(rs)
            src = netaddr.IPNetwork(src)
            rd = netaddr.IPNetwork(rd)
            dst = netaddr.IPNetwork(dst)
            # check if cidrs are affected by rule first
            if (int(dst.network) >= int(rd.broadcast) or
                    int(dst.broadcast) <= int(rd.network) or
                    int(src.network) >= int(rs.broadcast) or
                    int(src.broadcast) <= int(rs.network)):
                continue

            # skip matching rules for 'any' and 'external' networks
            if (str(dst) == '0.0.0.0/0' and str(rd) != '0.0.0.0/0'):
                continue
            if (str(src) == '0.0.0.0/0' and str(rs) != '0.0.0.0/0'):
                continue

            # external network rules only affect external traffic
            if (rule['source'] == 'external' and
                    src_rulename not in v4_any_words):
                continue
            if (rule['destination'] == 'external' and
                    dst_rulename not in v4_any_words):
                continue

            match = {'bitsinsrc': rs.prefixlen,
                     'bitsindst': rd.prefixlen,
                     'rule': rule}
            matchingrules.append(match)

        if not matchingrules:
            connectivity['reachable'] = 'none'
            connectivity['inverse_rule'] = {'source': src_rulename,
                                            'destination': dst_rulename,
                                            'action': 'permit'}
            return connectivity

        sortedrules = sorted(matchingrules,
                             key=lambda k: (k['bitsinsrc'], k['bitsindst']),
                             reverse=True)
        match = sortedrules[0]
        if (match['bitsinsrc'] > src.prefixlen or
                match['bitsindst'] > dst.prefixlen):
            connectivity['reachable'] = 'partial'
            connectivity['conflicting_rule'] = match['rule']
            return connectivity

        if (match['rule']['source'] == src_rulename and
                match['rule']['destination'] == dst_rulename):
            connectivity['rule_to_delete'] = match['rule']

        if match['rule']['action'] == 'permit':
            connectivity['reachable'] = 'full'
            inverseaction = 'deny'
        else:
            connectivity['reachable'] = 'none'
            inverseaction = 'permit'
        connectivity['inverse_rule'] = {'source': src_rulename,
                                        'destination': dst_rulename,
                                        'action': inverseaction}
        return connectivity

    def get_routerrules_data(self, checksupport=False):
        try:
            routerrules = getattr(self.tab_group.kwargs['router'],
                                  'router_rules')
            supported = True
        except Exception:
            routerrules = []
            supported = False

        if checksupport:
            return routerrules, supported
        return routerrules
