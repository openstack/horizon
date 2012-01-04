# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright 2011 Nebula, Inc.
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

from __future__ import absolute_import

import copy

from django import template

from horizon.base import Horizon


register = template.Library()


@register.filter
def can_haz(user, component):
    """ Checks if the given user has the necessary roles for the component. """
    if hasattr(user, 'roles'):
        user_roles = set([role['name'].lower() for role in user.roles])
    else:
        user_roles = set([])
    if set(getattr(component, 'roles', [])) <= user_roles:
        return True
    return False


@register.inclusion_tag('horizon/_nav_list.html', takes_context=True)
def horizon_main_nav(context):
    """ Generates top-level dashboard navigation entries. """
    if 'request' not in context:
        return {}
    current_dashboard = context['request'].horizon.get('dashboard', None)
    dashboards = []
    for dash in Horizon.get_dashboards():
        if callable(dash.nav) and dash.nav(context):
            dashboards.append(dash)
        elif dash.nav:
            dashboards.append(dash)
    return {'components': dashboards,
            'user': context['request'].user,
            'current': getattr(current_dashboard, 'slug', None)}


@register.inclusion_tag('horizon/_subnav_list.html', takes_context=True)
def horizon_dashboard_nav(context):
    """ Generates sub-navigation entries for the current dashboard. """
    if 'request' not in context:
        return {}
    dashboard = context['request'].horizon['dashboard']
    if isinstance(dashboard.panels, dict):
        panels = copy.copy(dashboard.get_panels())
    else:
        panels = {dashboard.name: dashboard.get_panels()}

    for heading, items in panels.iteritems():
        temp_panels = []
        for panel in items:
            if callable(panel.nav) and panel.nav(context):
                temp_panels.append(panel)
            elif not callable(panel.nav) and panel.nav:
                temp_panels.append(panel)
        panels[heading] = temp_panels
    non_empty_panels = dict([(k, v) for k, v in panels.items() if len(v) > 0])
    return {'components': non_empty_panels,
            'user': context['request'].user,
            'current': context['request'].horizon['panel'].slug}
