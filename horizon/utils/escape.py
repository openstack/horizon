# Copyright 2016, Rackspace, US, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import json

import django.utils.html


def escape(text, existing=django.utils.html.escape):
    # Replace our angular markup string with a different string
    # (which just happens to be the Django comment string)
    # this prevents user-supplied data from being intepreted in
    # our pages by angularjs, thus preventing it from being used
    # for XSS attacks. Note that we use {$ $} instead of the
    # standard {{ }} - this is configured in horizon.framework
    # angularjs module through $interpolateProvider.
    return existing(text).replace('{$', '{%').replace('$}', '%}')


# this will be invoked as early as possible in settings.py
def monkeypatch_escape():
    django.utils.html.escape = escape


# Mirrors django.utils.html._json_script_escapes, which is private and so
# cannot be imported directly.
_JSON_SCRIPT_ESCAPES = {
    ord('>'): '\\u003E',
    ord('<'): '\\u003C',
    ord('&'): '\\u0026',
}


def json_dumps_for_script(value):
    """Serialize a value to JSON safe to embed in an inline <script> block.

    ``json.dumps()`` escapes the characters that matter to a JSON parser, but
    leaves ``<``, ``>`` and ``&`` untouched. A string value containing a
    literal ``</script>`` therefore closes the surrounding script element,
    because a browser tokenizes the element boundaries before any JavaScript
    runs, and everything after it becomes markup. Escaping those three
    characters as unicode sequences leaves the decoded JSON value unchanged
    while making it inert to the HTML parser.
    """
    return json.dumps(value).translate(_JSON_SCRIPT_ESCAPES)
