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

from __future__ import division

from csv import DictWriter  # noqa
from csv import writer  # noqa


from django.http import HttpResponse  # noqa
from django.http import StreamingHttpResponse  # noqa
from django import template as django_template
import six

from six import StringIO


class CsvDataMixin(object):

    """CSV data Mixin - provides handling for CSV data.

    .. attribute:: columns

        A list of CSV column definitions. If omitted - no column titles
        will be shown in the result file. Optional.
    """
    def __init__(self):
        self.out = StringIO()
        super(CsvDataMixin, self).__init__()
        if hasattr(self, "columns"):
            columns = [self.encode(col) for col in self.columns]
            self.writer = DictWriter(self.out, columns)
            self.is_dict = True
        else:
            self.writer = writer(self.out)
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
        value = six.text_type(value)
        if six.PY2:
            # csv and StringIO cannot work with mixed encodings,
            # so encode all with utf-8
            value = value.encode('utf-8')
        return value


class BaseCsvResponse(CsvDataMixin, HttpResponse):

    """Base CSV response class. Provides handling of CSV data."""

    def __init__(self, request, template, context, content_type, **kwargs):
        super(BaseCsvResponse, self).__init__()
        self['Content-Disposition'] = 'attachment; filename="%s"' % (
            kwargs.get("filename", "export.csv"),)
        self['Content-Type'] = content_type
        self.context = context
        self.header = None
        if template:
            # Display some header info if provided as a template
            header_template = django_template.loader.get_template(template)
            context = django_template.RequestContext(request, self.context)
            self.header = header_template.render(context)

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
        super(BaseCsvStreamingResponse, self).__init__()
        self['Content-Disposition'] = 'attachment; filename="%s"' % (
            kwargs.get("filename", "export.csv"),)
        self['Content-Type'] = content_type
        self.context = context
        self.header = None
        if template:
            # Display some header info if provided as a template
            header_template = django_template.loader.get_template(template)
            context = django_template.RequestContext(request, self.context)
            self.header = header_template.render(context)

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
