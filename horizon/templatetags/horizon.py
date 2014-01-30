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

from django import template
from django.utils.datastructures import SortedDict
from django.utils.encoding import force_unicode
from django.utils.translation import ugettext_lazy as _

from horizon.base import Horizon  # noqa
from horizon import conf


register = template.Library()


@register.filter
def has_permissions(user, component):
    """Checks if the given user meets the permissions requirements for
    the component.
    """
    return user.has_perms(getattr(component, 'permissions', set()))


@register.filter
def has_permissions_on_list(components, user):
    return [component for component
                in components if has_permissions(user, component)]


@register.inclusion_tag('horizon/_accordion_nav.html', takes_context=True)
def horizon_nav(context):
    if 'request' not in context:
        return {}
    current_dashboard = context['request'].horizon.get('dashboard', None)
    current_panel = context['request'].horizon.get('panel', None)
    dashboards = []
    for dash in Horizon.get_dashboards():
        panel_groups = dash.get_panel_groups()
        non_empty_groups = []
        for group in panel_groups.values():
            allowed_panels = []
            for panel in group:
                if callable(panel.nav) and panel.nav(context):
                    allowed_panels.append(panel)
                elif not callable(panel.nav) and panel.nav:
                    allowed_panels.append(panel)
            if allowed_panels:
                non_empty_groups.append((group.name, allowed_panels))
        if callable(dash.nav) and dash.nav(context):
            dashboards.append((dash, SortedDict(non_empty_groups)))
        elif not callable(dash.nav) and dash.nav:
            dashboards.append((dash, SortedDict(non_empty_groups)))
    return {'components': dashboards,
            'user': context['request'].user,
            'current': current_dashboard,
            'current_panel': current_panel.slug if current_panel else '',
            'request': context['request']}


@register.inclusion_tag('horizon/_nav_list.html', takes_context=True)
def horizon_main_nav(context):
    """Generates top-level dashboard navigation entries."""
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
            'current': current_dashboard,
            'request': context['request']}


@register.inclusion_tag('horizon/_subnav_list.html', takes_context=True)
def horizon_dashboard_nav(context):
    """Generates sub-navigation entries for the current dashboard."""
    if 'request' not in context:
        return {}
    dashboard = context['request'].horizon['dashboard']
    panel_groups = dashboard.get_panel_groups()
    non_empty_groups = []

    for group in panel_groups.values():
        allowed_panels = []
        for panel in group:
            if callable(panel.nav) and panel.nav(context):
                allowed_panels.append(panel)
            elif not callable(panel.nav) and panel.nav:
                allowed_panels.append(panel)
        if allowed_panels:
            non_empty_groups.append((group.name, allowed_panels))

    return {'components': SortedDict(non_empty_groups),
            'user': context['request'].user,
            'current': context['request'].horizon['panel'].slug,
            'request': context['request']}


@register.filter
def quota(val, units=None):
    if val == float("inf"):
        return _("No Limit")
    elif units is not None:
        return "%s %s %s" % (val, units, force_unicode(_("Available")))
    else:
        return "%s %s" % (val, force_unicode(_("Available")))


@register.filter
def quotainf(val, units=None):
    if val == float("inf"):
        return _("No Limit")
    elif units is not None:
        return "%s %s" % (val, units)
    else:
        return val


class JSTemplateNode(template.Node):
    """Helper node for the ``jstemplate`` template tag."""
    def __init__(self, nodelist):
        self.nodelist = nodelist

    def render(self, context, ):
        output = self.nodelist.render(context)
        output = output.replace('[[[', '{{{').replace(']]]', '}}}')
        output = output.replace('[[', '{{').replace(']]', '}}')
        output = output.replace('[%', '{%').replace('%]', '%}')
        return output


@register.tag
def jstemplate(parser, token):
    """Replaces ``[[[`` and ``]]]`` with ``{{{`` and ``}}}``,
    ``[[`` and ``]]`` with ``{{`` and ``}}``  and
    ``[%`` and ``%]`` with ``{%`` and ``%}`` to avoid conflicts
    with Django's template engine when using any of the Mustache-based
    templating libraries.
    """
    nodelist = parser.parse(('endjstemplate',))
    parser.delete_first_token()
    return JSTemplateNode(nodelist)


@register.assignment_tag
def load_config():
    return conf.HORIZON_CONFIG
