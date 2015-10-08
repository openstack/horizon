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

from collections import OrderedDict
from horizon.contrib import bootstrap_datepicker

from django.conf import settings
from django import template
from django.template import Node
from django.utils.encoding import force_text
from django.utils import translation
from django.utils.translation import ugettext_lazy as _

from horizon.base import Horizon  # noqa
from horizon import conf

register = template.Library()


class MinifiedNode(Node):
    def __init__(self, nodelist):
        self.nodelist = nodelist

    def render(self, context):
        return ' '.join(
            force_text(self.nodelist.render(context).strip()).split()
        )


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


@register.inclusion_tag('horizon/_sidebar.html', takes_context=True)
def horizon_nav(context):
    if 'request' not in context:
        return {}
    current_dashboard = context['request'].horizon.get('dashboard', None)
    current_panel_group = None
    current_panel = context['request'].horizon.get('panel', None)
    dashboards = []
    for dash in Horizon.get_dashboards():
        panel_groups = dash.get_panel_groups()
        non_empty_groups = []
        for group in panel_groups.values():
            allowed_panels = []
            for panel in group:
                if (callable(panel.nav) and panel.nav(context) and
                        panel.can_access(context)):
                    allowed_panels.append(panel)
                elif (not callable(panel.nav) and panel.nav and
                        panel.can_access(context)):
                    allowed_panels.append(panel)
                if panel == current_panel:
                    current_panel_group = group.slug
            if allowed_panels:
                non_empty_groups.append((group, allowed_panels))
        if (callable(dash.nav) and dash.nav(context) and
                dash.can_access(context)):
            dashboards.append((dash, OrderedDict(non_empty_groups)))
        elif (not callable(dash.nav) and dash.nav and
                dash.can_access(context)):
            dashboards.append((dash, OrderedDict(non_empty_groups)))
    return {'components': dashboards,
            'user': context['request'].user,
            'current': current_dashboard,
            'current_panel_group': current_panel_group,
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
        if dash.can_access(context):
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
            if (callable(panel.nav) and panel.nav(context) and
                    panel.can_access(context)):
                allowed_panels.append(panel)
            elif (not callable(panel.nav) and panel.nav and
                    panel.can_access(context)):
                allowed_panels.append(panel)
        if allowed_panels:
            if group.name is None:
                non_empty_groups.append((dashboard.name, allowed_panels))
            else:
                non_empty_groups.append((group.name, allowed_panels))

    return {'components': OrderedDict(non_empty_groups),
            'user': context['request'].user,
            'current': context['request'].horizon['panel'].slug,
            'request': context['request']}


@register.filter
def quota(val, units=None):
    if val == float("inf"):
        return _("(No Limit)")
    elif units is not None:
        return "%s %s %s" % (val, force_text(units),
                             force_text(_("Available")))
    else:
        return "%s %s" % (val, force_text(_("Available")))


@register.filter
def quotainf(val, units=None):
    if val == float("inf"):
        return '-1'
    elif units is not None:
        return "%s %s" % (val, units)
    else:
        return val


@register.simple_tag
def quotapercent(used, limit):
    if used >= limit or limit == 0:
        return 100
    elif limit == float("inf"):
        return '[%s, true]' % used
    else:
        return round((float(used) / float(limit)) * 100)


class JSTemplateNode(template.Node):
    """Helper node for the ``jstemplate`` template tag."""
    def __init__(self, nodelist):
        self.nodelist = nodelist

    def render(self, context,):
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
    return conf


@register.assignment_tag
def datepicker_locale():
    locale_mapping = getattr(settings, 'DATEPICKER_LOCALES',
                             bootstrap_datepicker.LOCALE_MAPPING)
    return locale_mapping.get(translation.get_language(), 'en')


@register.tag
def minifyspace(parser, token):
    """Removes whitespace including tab and newline characters. Do not use this
    if you are using a <pre> tag

    Example usage::

        {% minifyspace %}
            <p>
                <a title="foo"
                   href="foo/">
                     Foo
                </a>
            </p>
        {% endminifyspace %}

    This example would return this HTML::

        <p><a title="foo" href="foo/">Foo</a></p>
    """
    nodelist = parser.parse(('endminifyspace',))
    parser.delete_first_token()
    return MinifiedNode(nodelist)
