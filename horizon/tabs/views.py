# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

from django import http

from horizon import exceptions
from horizon import tables
from horizon.tabs.base import TableTab  # noqa
from horizon import views


class TabView(views.HorizonTemplateView):
    """A generic class-based view for displaying a
    :class:`horizon.tabs.TabGroup`.

    This view handles selecting specific tabs and deals with AJAX requests
    gracefully.

    .. attribute:: tab_group_class

        The only required attribute for ``TabView``. It should be a class which
        inherits from :class:`horizon.tabs.TabGroup`.
    """
    tab_group_class = None
    _tab_group = None

    def __init__(self):
        if not self.tab_group_class:
            raise AttributeError("You must set the tab_group_class attribute "
                                 "on %s." % self.__class__.__name__)

    def get_tabs(self, request, **kwargs):
        """Returns the initialized tab group for this view."""
        if self._tab_group is None:
            self._tab_group = self.tab_group_class(request, **kwargs)
        return self._tab_group

    def get_context_data(self, **kwargs):
        """Adds the ``tab_group`` variable to the context data."""
        context = super(TabView, self).get_context_data(**kwargs)
        try:
            tab_group = self.get_tabs(self.request, **kwargs)
            context["tab_group"] = tab_group
            # Make sure our data is pre-loaded to capture errors.
            context["tab_group"].load_tab_data()
        except Exception:
            exceptions.handle(self.request)
        return context

    def handle_tabbed_response(self, tab_group, context):
        """Sends back an AJAX-appropriate response for the tab group if
        required, otherwise renders the response as normal.
        """
        if self.request.is_ajax():
            if tab_group.selected:
                return http.HttpResponse(tab_group.selected.render())
            else:
                return http.HttpResponse(tab_group.render())
        return self.render_to_response(context)

    def get(self, request, *args, **kwargs):
        context = self.get_context_data(**kwargs)
        return self.handle_tabbed_response(context["tab_group"], context)

    def render_to_response(self, *args, **kwargs):
        response = super(TabView, self).render_to_response(*args, **kwargs)
        # Because Django's TemplateView uses the TemplateResponse class
        # to provide deferred rendering (which is usually helpful), if
        # a tab group raises an Http302 redirect (from exceptions.handle for
        # example) the exception is actually raised *after* the final pass
        # of the exception-handling middleware.
        response.render()
        return response


class TabbedTableView(tables.MultiTableMixin, TabView):
    def __init__(self, *args, **kwargs):
        super(TabbedTableView, self).__init__(*args, **kwargs)
        self.table_classes = []
        self._table_dict = {}

    def load_tabs(self):
        """Loads the tab group, and compiles the table instances for each
        table attached to any :class:`horizon.tabs.TableTab` instances on
        the tab group. This step is necessary before processing any
        tab or table actions.
        """
        tab_group = self.get_tabs(self.request, **self.kwargs)
        tabs = tab_group.get_tabs()
        for tab in [t for t in tabs if issubclass(t.__class__, TableTab)]:
            self.table_classes.extend(tab.table_classes)
            for table in tab._tables.values():
                self._table_dict[table._meta.name] = {'table': table,
                                                      'tab': tab}

    def get_tables(self):
        """A no-op on this class. Tables are handled at the tab level."""
        # Override the base class implementation so that the MultiTableMixin
        # doesn't freak out. We do the processing at the TableTab level.
        return {}

    def handle_table(self, table_dict):
        """For the given dict containing a ``DataTable`` and a ``TableTab``
        instance, it loads the table data for that tab and calls the
        table's :meth:`~horizon.tables.DataTable.maybe_handle` method. The
        return value will be the result of ``maybe_handle``.
        """
        table = table_dict['table']
        tab = table_dict['tab']
        tab.load_table_data()
        table_name = table._meta.name
        tab._tables[table_name]._meta.has_prev_data = self.has_prev_data(table)
        tab._tables[table_name]._meta.has_more_data = self.has_more_data(table)
        handled = tab._tables[table_name].maybe_handle()
        return handled

    def get(self, request, *args, **kwargs):
        self.load_tabs()
        # Gather our table instances. It's important that they're the
        # actual instances and not the classes!
        table_instances = [t['table'] for t in self._table_dict.values()]
        # Early out before any tab or table data is loaded
        for table in table_instances:
            preempted = table.maybe_preempt()
            if preempted:
                return preempted

        # If we have an action, determine if it belongs to one of our tables.
        # We don't iterate through all of the tables' maybes_handle
        # methods; just jump to the one that's got the matching name.
        table_name, action, obj_id = tables.DataTable.check_handler(request)
        if table_name in self._table_dict:
            handled = self.handle_table(self._table_dict[table_name])
            if handled:
                return handled

        context = self.get_context_data(**kwargs)
        return self.handle_tabbed_response(context["tab_group"], context)

    def post(self, request, *args, **kwargs):
        # Direct POST to its appropriate tab
        # Note some table actions like filter do not have an 'action'
        if 'action' in request.POST:
            targetslug = request.POST['action'].split('__')[0]
            tabs = self.get_tabs(self.request, **self.kwargs).get_tabs()
            matches = [tab for tab in tabs if tab.slug == targetslug]
            if matches:
                # Call POST on first match only. There shouldn't be a case
                # where multiple tabs have the same slug and processing the
                # request twice could lead to unpredictable behavior.
                matches[0].post(request, *args, **kwargs)

        # GET and POST handling are the same
        return self.get(request, *args, **kwargs)
