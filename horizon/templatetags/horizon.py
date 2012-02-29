# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright 2012 Nebula, Inc.
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
    """
    Checks if the given user meets the requirements for the component. This
    includes both user roles and services in the service catalog.
    """
    if hasattr(user, 'roles'):
        user_roles = set([role['name'].lower() for role in user.roles])
    else:
        user_roles = set([])
    roles_statisfied = set(getattr(component, 'roles', [])) <= user_roles

    if hasattr(user, 'roles'):
        services = set([service['type'] for service in user.service_catalog])
    else:
        services = set([])
    services_statisfied = set(getattr(component, 'services', [])) <= services

    if roles_statisfied and services_statisfied:
        return True
    return False


@register.filter
def can_haz_list(components, user):
    return [component for component in components if can_haz(user, component)]


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


@register.inclusion_tag('horizon/common/_progress_bar.html')
def horizon_progress_bar(current_val, max_val):
    """ Renders a progress bar based on parameters passed to the tag. The first
    parameter is the current value and the second is the max value.

    Example: ``{% progress_bar 25 50 %}``

    This will generate a half-full progress bar.

    The rendered progress bar will fill the area of its container. To constrain
    the rendered size of the bar provide a container with appropriate width and
    height styles.

    """
    return {'current_val': current_val,
            'max_val': max_val}


class JSTemplateNode(template.Node):
    """ Helper node for the ``jstemplate`` template tag. """
    def __init__(self, nodelist):
        self.nodelist = nodelist

    def render(self, context, ):
        output = self.nodelist.render(context)
        return output.replace('[[', '{{').replace(']]', '}}')


@register.tag
def jstemplate(parser, token):
    """
    Replaces ``[[`` and ``]]`` with ``{{`` and ``}}`` to avoid conflicts
    with Django's template engine when using any of the Mustache-based
    templating libraries.
    """
    nodelist = parser.parse(('endjstemplate',))
    parser.delete_first_token()
    return JSTemplateNode(nodelist)
