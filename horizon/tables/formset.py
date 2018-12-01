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

import collections
import logging
import sys

import six

from django import template
from django.template import loader

from horizon.tables import base as horizon_tables


LOG = logging.getLogger(__name__)


class FormsetCell(horizon_tables.Cell):
    """A DataTable cell that knows about its field from the formset."""

    def __init__(self, *args, **kwargs):
        super(FormsetCell, self).__init__(*args, **kwargs)
        try:
            self.field = (self.row.form or {})[self.column.name]
        except KeyError:
            self.field = None
        else:
            if self.field.errors:
                self.attrs['class'] = (self.attrs.get('class', '') +
                                       ' error form-group')
                self.attrs['title'] = ' '.join(
                    six.text_type(error) for error in self.field.errors)


class FormsetRow(horizon_tables.Row):
    """A DataTable row that knows about its form from the formset."""

    template_path = 'horizon/common/_formset_table_row.html'

    def __init__(self, column, datum, form):
        self.form = form
        super(FormsetRow, self).__init__(column, datum)
        if not self.cells:
            # We need to be able to handle empty rows, because there may
            # be extra empty forms in a formset. The original DataTable breaks
            # on this, because it sets self.cells to [], but later expects a
            # OrderedDict. We just fill self.cells with empty Cells.
            cells = []
            for col in self.table.columns.values():
                cell = self.table._meta.cell_class(None, col, self)
                cells.append((col.name or col.auto, cell))
            self.cells = collections.OrderedDict(cells)

    def render(self):
        return loader.render_to_string(self.template_path,
                                       {"row": self, "form": self.form})


class FormsetDataTableMixin(object):
    """A mixin for DataTable to support Django Formsets.

    This works the same as the ``FormsetDataTable`` below, but can be used
    to add to existing DataTable subclasses.
    """
    formset_class = None

    def __init__(self, *args, **kwargs):
        super(FormsetDataTableMixin, self).__init__(*args, **kwargs)
        self._formset = None

        # Override Meta settings, because we need custom Form and Cell classes,
        # and also our own template.
        self._meta.row_class = FormsetRow
        self._meta.cell_class = FormsetCell
        self._meta.template = 'horizon/common/_formset_table.html'

    def get_required_columns(self):
        """Lists names of columns that have required fields."""
        required_columns = []
        if self.formset_class:
            empty_form = self.get_formset().empty_form
            for column in self.columns.values():
                field = empty_form.fields.get(column.name)
                if field and field.required:
                    required_columns.append(column.name)
        return required_columns

    def _get_formset_data(self):
        """Formats the self.filtered_data in a way suitable for a formset."""
        data = []
        for datum in self.filtered_data:
            form_data = {}
            for column in self.columns.values():
                value = column.get_data(datum)
                form_data[column.name] = value
            form_data['id'] = self.get_object_id(datum)
            data.append(form_data)
        return data

    def get_formset(self):
        """Provide the formset corresponding to this DataTable.

        Use this to validate the formset and to get the submitted data back.
        """
        if self._formset is None:
            self._formset = self.formset_class(
                self.request.POST or None,
                initial=self._get_formset_data(),
                prefix=self._meta.name)
        return self._formset

    def get_empty_row(self):
        """Return a row with no data, for adding at the end of the table."""
        return self._meta.row_class(self, None, self.get_formset().empty_form)

    def get_rows(self):
        """Return the row data for this table broken out by columns.

        The row objects get an additional ``form`` parameter, with the
        formset form corresponding to that row.
        """
        try:
            rows = []
            if self.formset_class is None:
                formset = []
            else:
                formset = self.get_formset()
                formset.is_valid()
            for datum, form in six.moves.zip_longest(self.filtered_data,
                                                     formset):
                row = self._meta.row_class(self, datum, form)
                if self.get_object_id(datum) == self.current_item_id:
                    self.selected = True
                    row.classes.append('current_selected')
                rows.append(row)
        except Exception:
            # Exceptions can be swallowed at the template level here,
            # re-raising as a TemplateSyntaxError makes them visible.
            LOG.exception("Error while rendering table rows.")
            exc_info = sys.exc_info()
            raise six.reraise(template.TemplateSyntaxError, exc_info[1],
                              exc_info[2])
        return rows

    def get_object_id(self, datum):
        # We need to support ``None`` when there are more forms than data.
        if datum is None:
            return None
        return super(FormsetDataTableMixin, self).get_object_id(datum)


class FormsetDataTable(FormsetDataTableMixin, horizon_tables.DataTable):
    """A DataTable with support for Django Formsets.

    Note that :attr:`horizon.tables.DataTableOptions.row_class` and
    :attr:`horizon.tables.DataTaleOptions.cell_class` are overwritten in this
    class, so setting them in ``Meta`` has no effect.

    .. attribute:: formset_class

        A class made with ``django.forms.formsets.formset_factory``
        containing the definition of the formset to use with this data table.

        The columns that are named the same as the formset fields will be
        replaced with form widgets in the table. Any hidden fields from the
        formset will also be included. The fields that are not hidden and
        don't correspond to any column will not be included in the form.
    """
