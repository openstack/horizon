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

"""
A set of custom types for oslo.config.
"""

import ast
import os
import re

import six

from django.utils import encoding
from django.utils import functional
from django.utils.module_loading import import_string
from django.utils.translation import pgettext_lazy
from oslo_config import types


class Maybe(types.ConfigType):
    """A custom option type for a value that may be None."""

    def __init__(self, type_):
        self.type_ = type_
        type_name = getattr(type_, 'type_name', 'unknown value')
        super(Maybe, self).__init__('optional %s' % type_name)

    def __call__(self, value):
        if value is None:
            return None
        return self.type_(value)

    def _formatter(self, value):
        if value is None:
            return ''
        return self.type_._formatter(value)


class URL(types.ConfigType):
    """A custom option type for a URL or part of URL."""

    CLEAN_SLASH_RE = re.compile(r'(?<!:)//')

    def __init__(self):
        super(URL, self).__init__('web URL')

    def __call__(self, value):
        if not isinstance(value, six.string_types):
            raise ValueError("Expected URL.")
        value = re.sub(self.CLEAN_SLASH_RE, '/', value)
        if not value.endswith('/'):
            value += '/'
        return value

    def _formatter(self, value):
        return self.quote_trailing_and_leading_space(value)


class Path(types.ConfigType):
    """A custom option type for a path to file."""

    def __init__(self):
        super(Path, self).__init__('filesystem path')

    def __call__(self, value):
        if not isinstance(value, six.string_types):
            raise ValueError("Expected file path.")
        return os.path.normpath(value)

    def _formatter(self, value):
        return self.quote_trailing_and_leading_space(value)


class Translate(types.ConfigType):
    """A custom option type for translatable strings."""

    def __init__(self, hint=None):
        self.hint = hint
        super(Translate, self).__init__('translatable string')

    def __call__(self, value):
        if not isinstance(value, six.string_types):
            return value
        return pgettext_lazy(value, self.hint)

    def _formatter(self, value):
        return self.quote_trailing_and_leading_space(
            encoding.force_text(value))


class Literal(types.ConfigType):
    """A custom option type for a Python literal."""

    def __init__(self, spec=None):
        self.spec = spec
        super(Literal, self).__init__('python literal')

    def __call__(self, value):
        if isinstance(value, six.string_types):
            try:
                value = ast.literal_eval(value)
            except SyntaxError as e:
                six.raise_from(ValueError(e), e)
        self.validate(value, self.spec)
        return self.update(value, self.spec)

    def validate(self, result, spec):  # noqa Yes, it's too complex.
        """Validate that the result has the correct structure."""
        if spec is None:
            # None matches anything.
            return
        if isinstance(spec, dict):
            if not isinstance(result, dict):
                raise ValueError('Dictionary expected, but %r found.' % result)
            if spec:
                spec_value = next(iter(spec.values()))  # Yay Python 3!
                for value in result.values():
                    self.validate(value, spec_value)
                spec_key = next(iter(spec.keys()))
                for key in result:
                    self.validate(key, spec_key)
        if isinstance(spec, list):
            if not isinstance(result, list):
                raise ValueError('List expected, but %r found.' % result)
            if spec:
                for value in result:
                    self.validate(value, spec[0])
        if isinstance(spec, tuple):
            if not isinstance(result, tuple):
                raise ValueError('Tuple expected, but %r found.' % result)
            if len(result) != len(spec):
                raise ValueError('Expected %d elements in tuple %r.' %
                                 (len(spec), result))
            for s, value in zip(spec, result):
                self.validate(value, s)
        if isinstance(spec, six.string_types):
            if not isinstance(result, six.string_types):
                raise ValueError('String expected, but %r found.' % result)
        if isinstance(spec, int):
            if not isinstance(result, int):
                raise ValueError('Integer expected, but %r found.' % result)
        if isinstance(spec, bool):
            if not isinstance(result, bool):
                raise ValueError('Boolean expected, but %r found.' % result)

    def update(self, result, spec):
        """Replace elements with results of calling callables."""
        if isinstance(spec, dict):
            if spec:
                spec_value = next(iter(spec.values()))
                for key, value in result.items():
                    result[key] = self.update(value, spec_value)
        if isinstance(spec, list):
            if spec:
                for i, value in enumerate(result):
                    result[i] = self.update(value, spec[0])
        if isinstance(spec, tuple):
            return tuple(self.update(value, s)
                         for s, value in zip(spec, result))
        if callable(spec):
            return spec(result)
        return result

    def _format(self, result):
        if isinstance(result, dict):
            return '{%s}' % ', '.join(
                '%s: %s' % (key, self._format(value))
                for key, value in result.items()
            )
        if isinstance(result, list):
            return '[%s]' % ', '.join(self._format(value) for value in result)
        if isinstance(result, tuple):
            return '(%s)' % ', '.join(self._format(value) for value in result)
        if isinstance(result, functional.Promise):
            # Lazy translatable string.
            return repr(encoding.force_text(result))
        return repr(result)

    def _formatter(self, value):
        # We need to walk the lists and dicts to handle the Django lazy
        # translatable strings inside.
        return self._format(value)


class Importable(types.ConfigType):
    """A custom option type for an importable python object."""

    def __init__(self):
        super(Importable, self).__init__('importable python object')

    def __call__(self, value):
        if not isinstance(value, six.string_types):
            # Already imported.
            return value
        try:
            return import_string(value)
        except ImportError as e:
            six.raise_from(ValueError(e), e)

    def _formatter(self, value):
        module = value.__module__
        name = value.__name__
        return self.quote_trailing_and_leading_space('%s.%s' % (module, name))
