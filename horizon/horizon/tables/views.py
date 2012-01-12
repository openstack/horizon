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

from django.views import generic


class MultiTableView(generic.TemplateView):
    """
    A class-based generic view to handle the display and processing of
    multiple :class:`~horizon.tables.DataTable` classes in a single view.

    Three steps are required to use this view: set the ``table_classes``
    attribute with a tuple of the desired
    :class:`~horizon.tables.DataTable` classes;
    define a ``get_{{ table_name }}_data`` method for each table class
    which returns a set of data for that table; and specify a template for
    the ``template_name`` attribute.
    """
    def __init__(self, *args, **kwargs):
        super(MultiTableView, self).__init__(*args, **kwargs)
        self.table_classes = getattr(self, "table_classes", [])
        self._data = {}
        self._tables = {}

    def get_data(self):
        if not self._data:
            for table in self.table_classes:
                func_name = "get_%s_data" % table._meta.name
                data_func = getattr(self, func_name, None)
                if data_func is None:
                    cls_name = self.__class__.__name__
                    raise NotImplementedError("You must define a %s method "
                                              "on %s." % (func_name, cls_name))
                self._data[table._meta.name] = data_func()
        return self._data

    def get_tables(self):
        if not self.table_classes:
            raise AttributeError('You must specify a one or more DataTable '
                                 'classes for the "table_classes" attribute '
                                 'on %s.' % self.__class__.__name__)
        if not self._tables:
            for table in self.table_classes:
                func_name = "get_%s_table" % table._meta.name
                table_func = getattr(self, func_name, None)
                data = self.get_data()[table._meta.name]
                if table_func is None:
                    tbl = table(self.request, data)
                else:
                    tbl = table_func(self, self.request, data)
                self._tables[table._meta.name] = tbl
        return self._tables

    def get_context_data(self, **kwargs):
        context = super(MultiTableView, self).get_context_data(**kwargs)
        tables = self.get_tables()
        for name, table in tables.items():
            context["%s_table" % name] = table
        return context

    def get(self, request, *args, **kwargs):
        context = self.get_context_data(**kwargs)
        return self.render_to_response(context)

    def post(self, request, *args, **kwargs):
        tables = self.get_tables().values()
        for table in tables:
            handled = table.maybe_handle()
            if handled:
                return handled
        return self.get(request, *args, **kwargs)


class DataTableView(MultiTableView):
    """ A class-based generic view to handle basic DataTable processing.

    Three steps are required to use this view: set the ``table_class``
    attribute with the desired :class:`~horizon.tables.DataTable` class;
    define a ``get_data`` method which returns a set of data for the
    table; and specify a template for the ``template_name`` attribute.

    Optionally, you can override the ``has_more_data`` method to trigger
    pagination handling for APIs that support it.
    """
    table_class = None
    context_object_name = 'table'

    def get_data(self):
        raise NotImplementedError('You must define a "get_data" method on %s.'
                                  % self.__class__.__name__)

    def has_more_data(self):
        return False

    def get_tables(self):
        table = self.get_table()
        return {table._meta.name: table}

    def get_table(self):
        if not self.table_class:
            raise AttributeError('You must specify a DataTable class for the '
                                 '"table_class" attribute on %s.'
                                 % self.__class__.__name__)
        if not hasattr(self, "table"):
            self.table = self.table_class(self.request,
                                          self.get_data(),
                                          **self.kwargs)
            self.table._meta.has_more_data = self.has_more_data()
        return self.table

    def get_context_data(self, **kwargs):
        context = super(DataTableView, self).get_context_data(**kwargs)
        context[self.context_object_name] = self.table
        return context
