#    Copyright (c) 2015 Mirantis, Inc.
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
import json
import json.encoder as encoder

from django.utils.translation import ugettext_lazy as _
import six


class NaNJSONEncoder(json.JSONEncoder):
    def __init__(self, nan_str='NaN', inf_str='1e+999', **kwargs):
        self.nan_str = nan_str
        self.inf_str = inf_str
        super(NaNJSONEncoder, self).__init__(**kwargs)

    def iterencode(self, o, _one_shot=False):
        """The sole purpose of defining a custom JSONEncoder class is to
        override floatstr() inner function, or more specifically the
        representation of NaN and +/-float('inf') values in a JSON. Although
        Infinity values are not supported by JSON standard, we still can
        convince Javascript JSON.parse() to create a Javascript Infinity
        object if we feed a token `1e+999` to it.
        """
        if self.check_circular:
            markers = {}
        else:
            markers = None

        if self.ensure_ascii:
            _encoder = encoder.encode_basestring_ascii
        else:
            _encoder = encoder.encode_basestring

        # On Python 3, JSONEncoder has no more encoding attribute, it produces
        # an Unicode string
        if six.PY2 and self.encoding != 'utf-8':
            def _encoder(o, _orig_encoder=_encoder, _encoding=self.encoding):
                if isinstance(o, str):
                    o = o.decode(_encoding)
                return _orig_encoder(o)

        def floatstr(o, allow_nan=self.allow_nan, _repr=encoder.FLOAT_REPR,
                     _inf=encoder.INFINITY, _neginf=-encoder.INFINITY):
            # Check for specials.  Note that this type of test is processor
            # and/or platform-specific, so do tests which don't depend on the
            # internals.

            if o != o:
                text = self.nan_str
            elif o == _inf:
                text = self.inf_str
            elif o == _neginf:
                text = '-' + self.inf_str
            else:
                return _repr(o)

            if not allow_nan:
                raise ValueError(
                    _("Out of range float values are not JSON compliant: %r") %
                    o)

            return text

        _iterencode = json.encoder._make_iterencode(
            markers, self.default, _encoder, self.indent, floatstr,
            self.key_separator, self.item_separator, self.sort_keys,
            self.skipkeys, _one_shot)
        return _iterencode(o, 0)
