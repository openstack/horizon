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

import csv
import io

from django.http import HttpResponse
from django.http import StreamingHttpResponse
from django import template as django_template


class CsvDataMixin(object):

    """CSV data Mixin - provides handling for CSV data.

    .. attribute:: columns

        A list of CSV column definitions. If omitted - no column titles
        will be shown in the result file. Optional.
    """
    def __init__(self):
        self.out = io.StringIO()
        super().__init__()
        if hasattr(self, "columns"):
            columns = [self.encode(col) for col in self.columns]
            self.writer = csv.DictWriter(self.out, columns,
                                         quoting=csv.QUOTE_ALL)
            self.is_dict = True
        else:
            self.writer = csv.writer(self.out, quoting=csv.QUOTE_ALL)
            self.is_dict = False

    def write_csv_header(self):
        if self.is_dict:
            try:
                self.writer.writeheader()
            except AttributeError:
                # For Python<2.7
                self.writer.writerow(dict(zip(
                                          self.writer.fieldnames,
                                          self.writer.fieldnames)))

    def write_csv_row(self, args):
        if self.is_dict:
            self.writer.writerow(dict(zip(
                self.writer.fieldnames, [self.encode(col) for col in args])))
        else:
            self.writer.writerow([self.encode(col) for col in args])

    def encode(self, value):
        return str(value)


class BaseCsvResponse(CsvDataMixin, HttpResponse):

    """Base CSV response class. Provides handling of CSV data."""

    def __init__(self, request, template, context, content_type, **kwargs):
        super().__init__()
        self['Content-Disposition'] = 'attachment; filename="%s"' % (
            kwargs.get("filename", "export.csv"),)
        self['Content-Type'] = content_type
        self.context = context
        self.header = None
        if template:
            # Display some header info if provided as a template
            header_template = django_template.loader.get_template(template)
            self.header = header_template.render(self.context, request)

        if self.header:
            self.out.write(self.encode(self.header))

        self.write_csv_header()

        for row in self.get_row_data():
            self.write_csv_row(row)

        self.out.flush()
        self.content = self.out.getvalue()
        self.out.close()

    def get_row_data(self):
        return []


class BaseCsvStreamingResponse(CsvDataMixin, StreamingHttpResponse):

    """Base CSV Streaming class. Provides streaming response for CSV data."""

    def __init__(self, request, template, context, content_type, **kwargs):
        super().__init__()
        self['Content-Disposition'] = 'attachment; filename="%s"' % (
            kwargs.get("filename", "export.csv"),)
        self['Content-Type'] = content_type
        self.context = context
        self.header = None
        if template:
            # Display some header info if provided as a template
            header_template = django_template.loader.get_template(template)
            self.header = header_template.render(self.context, request)

        self._closable_objects.append(self.out)

        self.streaming_content = self.get_content()

    def buffer(self):
        buf = self.out.getvalue()
        self.out.truncate(0)
        return buf

    def get_content(self):
        if self.header:
            self.out.write(self.encode(self.header))

        self.write_csv_header()
        yield self.buffer()

        for row in self.get_row_data():
            self.write_csv_row(row)
            yield self.buffer()

    def get_row_data(self):
        return []
