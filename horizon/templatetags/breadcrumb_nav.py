# Copyright 2016 Cisco Systems, Inc.
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

from django import template

register = template.Library()


@register.inclusion_tag('bootstrap/breadcrumb.html',
                        takes_context=True)
def breadcrumb_nav(context):
    """A logic heavy function for automagically creating a breadcrumb.

    It uses the dashboard, panel group(if it exists), then current panel.
    Can also use a "custom_breadcrumb" context item to add extra items.
    """
    breadcrumb = []
    dashboard = context.request.horizon['dashboard']
    try:
        panel_groups = dashboard.get_panel_groups()
    except KeyError:
        panel_groups = None
    panel_group = None
    panel = context.request.horizon['panel']

    # Add panel group, if there is one
    if panel_groups:
        for group in panel_groups.values():
            if panel.slug in group.panels and group.slug != 'default':
                panel_group = group
                break

    # Remove panel reference if that is the current page
    if panel.get_absolute_url() == context.request.path:
        panel = None

    # Get custom breadcrumb, if there is one.
    custom_breadcrumb = context.get('custom_breadcrumb')

    # Build list of tuples (name, optional url)
    breadcrumb.append((dashboard.name, None))
    if panel_group:
        breadcrumb.append((panel_group.name, None))
    if panel:
        breadcrumb.append((panel.name, panel.get_absolute_url()))
    if custom_breadcrumb:
        breadcrumb.extend(custom_breadcrumb)
    breadcrumb.append((context.get('page_title'), None))

    return {'breadcrumb': breadcrumb}
