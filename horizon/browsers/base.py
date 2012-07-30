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

from django import template

from horizon.tables import DataTable
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

    .. attribute:: template

        String containing the template which should be used to render
        the browser. Defaults to ``"horizon/common/_resource_browser.html"``.

    .. attribute:: context_var_name

        The name of the context variable which will contain the browser when
        it is rendered. Defaults to ``"browser"``.
    """
    name = None
    verbose_name = None
    navigation_table_class = None
    content_table_class = None
    template = "horizon/common/_resource_browser.html"
    context_var_name = "browser"

    def __init__(self, request, tables=None, attrs=None,
                 **kwargs):
        super(ResourceBrowser, self).__init__()
        self.name = getattr(self, "name", self.__class__.__name__)
        self.verbose_name = getattr(self, "verbose_name", self.name.title())
        self.request = request
        self.attrs.update(attrs or {})

        self.navigation_table_class = getattr(self, "navigation_table_class",
                                              None)
        self.check_table_class(self.navigation_table_class,
                               "navigation_table_class")

        self.content_table_class = getattr(self, "content_table_class",
                                           None)
        self.check_table_class(self.content_table_class,
                               "content_table_class")

        self.set_tables(tables)

    def check_table_class(self, cls, attr_name):
        if not cls or not issubclass(cls, (DataTable, )):
            raise ValueError("You must specify a DataTable class for "
                             "the %s attribute on %s "
                             % (attr_name, self.__class__.__name__))

    def set_tables(self, tables):
        if tables:
            self.navigation_table = tables.get(self.navigation_table_class
                                                   ._meta.name, None)
            self.content_table = tables.get(self.content_table_class
                                                ._meta.name, None)
        else:
            raise ValueError("There are no tables passed to class %s." %
                             self.__class__.__name__)

    def render(self):
        browser_template = template.loader.get_template(self.template)
        extra_context = {self.context_var_name: self}
        context = template.RequestContext(self.request, extra_context)
        return browser_template.render(context)
