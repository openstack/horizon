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
