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

import inspect
import sys

import django.shortcuts
import django.views.defaults


def dispatcher(request, test_name):
    # import is included in this non-standard location to avoid
    # problems importing mox.  See bug/1288245
    from horizon.test.jasmine import jasmine_tests as tests
    classes = inspect.getmembers(sys.modules[tests.__name__],
                                 inspect.isclass)

    if not test_name:
        return django.shortcuts.render(
            request,
            "horizon/jasmine/index.html",
            {'classes': (cls_name for cls_name, _ in classes)}
        )
    else:
        for cls_name, cls in classes:
            if cls_name == test_name:
                template = cls.template_name

                if not template:
                    template = "horizon/jasmine/jasmine.html"

                return django.shortcuts.render(
                    request,
                    template,
                    {'specs': cls.specs, 'sources': cls.sources,
                     'externalTemplates': cls.externalTemplates})

    return django.views.defaults.page_not_found(request)
