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

from django import template
from django.utils.translation import ugettext_lazy as _

from horizon.browsers.breadcrumb import Breadcrumb  # noqa
from horizon.tables import DataTable  # noqa
from horizon.utils import html


class ResourceBrowser(html.HTMLElement):
    """A class which defines a browser for displaying data.

    .. attribute:: name

        A short name or slug for the browser.

    .. attribute:: verbose_name

        A more verbose name for the browser meant for display purposes.

    .. attribute:: navigation_table_class

        This table displays data on the left side of the browser.
        Set the ``navigation_table_class`` attribute with
        the desired :class:`~horizon.tables.DataTable` class.
        This table class must set browser_table attribute in Meta to
        ``"navigation"``.

    .. attribute:: content_table_class

        This table displays data on the right side of the browser.
        Set the ``content_table_class`` attribute with
        the desired :class:`~horizon.tables.DataTable` class.
        This table class must set browser_table attribute in Meta to
        ``"content"``.

    .. attribute:: navigation_kwarg_name

        This attribute represents the key of the navigatable items in the
        kwargs property of this browser's view.
        Defaults to ``"navigation_kwarg"``.

    .. attribute:: content_kwarg_name

        This attribute represents the key of the content items in the
        kwargs property of this browser's view.
        Defaults to ``"content_kwarg"``.

    .. attribute:: template

        String containing the template which should be used to render
        the browser. Defaults to ``"horizon/common/_resource_browser.html"``.

    .. attribute:: context_var_name

        The name of the context variable which will contain the browser when
        it is rendered. Defaults to ``"browser"``.

    .. attribute:: has_breadcrumb

        Indicates if the content table of the browser would have breadcrumb.
        Defaults to false.

    .. attribute:: breadcrumb_template

        This is a template used to render the breadcrumb.
        Defaults to ``"horizon/common/_breadcrumb.html"``.
    """
    name = None
    verbose_name = None
    navigation_table_class = None
    content_table_class = None
    navigation_kwarg_name = "navigation_kwarg"
    content_kwarg_name = "content_kwarg"
    navigable_item_name = _("Navigation Item")
    template = "horizon/common/_resource_browser.html"
    context_var_name = "browser"
    has_breadcrumb = False
    breadcrumb_template = "horizon/common/_breadcrumb.html"
    breadcrumb_url = None

    def __init__(self, request, tables_dict=None, attrs=None, **kwargs):
        super(ResourceBrowser, self).__init__()
        self.name = self.name or self.__class__.__name__
        self.verbose_name = self.verbose_name or self.name.title()
        self.request = request
        self.kwargs = kwargs
        self.has_breadcrumb = getattr(self, "has_breadcrumb")
        if self.has_breadcrumb:
            self.breadcrumb_template = getattr(self, "breadcrumb_template")
            self.breadcrumb_url = getattr(self, "breadcrumb_url")
            if not self.breadcrumb_url:
                raise ValueError("You must specify a breadcrumb_url "
                                 "if the has_breadcrumb is set to True.")
        self.attrs.update(attrs or {})
        self.check_table_class(self.content_table_class, "content_table_class")
        self.check_table_class(self.navigation_table_class,
                               "navigation_table_class")
        if tables_dict:
            self.set_tables(tables_dict)

    def check_table_class(self, cls, attr_name):
        if not cls or not issubclass(cls, DataTable):
            raise ValueError("You must specify a DataTable subclass for "
                             "the %s attribute on %s."
                             % (attr_name, self.__class__.__name__))

    def set_tables(self, tables):
        """Sets the table instances on the browser from a dictionary mapping
        table names to table instances (as constructed by MultiTableView).
        """
        self.navigation_table = tables[self.navigation_table_class._meta.name]
        self.content_table = tables[self.content_table_class._meta.name]
        navigation_item = self.kwargs.get(self.navigation_kwarg_name)
        content_path = self.kwargs.get(self.content_kwarg_name)
        if self.has_breadcrumb:
            self.prepare_breadcrumb(tables, navigation_item, content_path)

    def prepare_breadcrumb(self, tables, navigation_item, content_path):
        if self.has_breadcrumb and navigation_item and content_path:
            for table in tables.values():
                table.breadcrumb = Breadcrumb(self.request,
                                              self.breadcrumb_template,
                                              navigation_item,
                                              content_path,
                                              self.breadcrumb_url)

    def render(self):
        browser_template = template.loader.get_template(self.template)
        extra_context = {self.context_var_name: self}
        context = template.RequestContext(self.request, extra_context)
        return browser_template.render(context)
