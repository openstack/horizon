# Copyright 2015 Cisco Systems, Inc.
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

from django.conf import settings
from django.utils.translation import ugettext_lazy as _

from horizon import views


class IndexView(views.HorizonTemplateView):
    template_name = 'developer/theme_preview/index.html'
    page_title = _("Bootstrap Theme Preview")

    def get_context_data(self, **kwargs):
        theme_path = settings.CUSTOM_THEME_PATH
        context = super(IndexView, self).get_context_data(**kwargs)
        context['skin'] = theme_path.split('/')[-1]
        context['skin_desc'] = theme_path
        return context
