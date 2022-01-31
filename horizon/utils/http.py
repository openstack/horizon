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


def is_ajax(request):
    """Check if the request is AJAX-based.

    :param request: django.http.HttpRequest object
    :return: True if the request is AJAX-based.
    """
    # NOTE: Django 3.1 or later deprecates request.is_ajax() as it relied
    # on a jQuery-specific way of signifying AJAX calls,
    # but at the moment checking X-Requested-With header works in horizon.
    # If we adopt modern frameworks with JavaScript Fetch API,
    # we need to consider checking Accepts header as suggested in the
    # Django 3.1 release notes.
    # https://docs.djangoproject.com/en/4.0/releases/3.1/#id2
    # https://docs.djangoproject.com/en/3.1/ref/request-response/#django.http.HttpRequest.is_ajax
    return request.headers.get('x-requested-with') == 'XMLHttpRequest'
