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


class DataTableView(generic.TemplateView):
    """ A class-based generic view to handle basic DataTable processing.

    Three steps are required to use this view: set the ``table_class``
    attribute with the desired :class:`~horizon.tables.DataTable` class;
    define a ``get_data`` method which returns a set of data for the
    table; and specify a template for the ``template_name`` attribute.
    """
    table_class = None
    context_object_name = 'table'

    def get_data(self):
        raise NotImplementedError('You must define a "get_data" method on %s.'
                                  % self.__class__.__name__)

    def get_table(self):
        if not self.table_class:
            raise AttributeError('You must specify a DataTable class for the '
                                 '"table_class" attribute on %s.'
                                 % self.__class__.__name__)
        if not hasattr(self, "table"):
            self.table = self.table_class(self.request, self.get_data())
        return self.table

    def get(self, request, *args, **kwargs):
        table = self.get_table()
        context = self.get_context_data(**kwargs)
        context[self.context_object_name] = table
        return self.render_to_response(context)

    def post(self, request, *args, **kwargs):
        table = self.get_table()
        handled = table.maybe_handle()
        if handled:
            return handled
        return self.get(request, *args, **kwargs)
