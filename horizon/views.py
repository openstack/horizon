# Copyright 2012 Nebula, Inc.
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

from django import shortcuts
from django import template
from django.utils import encoding
from django.views import generic

import horizon
from horizon import exceptions


class PageTitleMixin(object):
    """A mixin that renders out a page title into a view.

    Many views in horizon have a page title that would ordinarily be
    defined and passed through in get_context_data function, this often
    leads to a lot of duplicated work in each view.

    This mixin standardises the process of defining a page title, letting
    views simply define a variable that is rendered into the context for
    them.

    There are cases when page title in a view may also display some context
    data, for that purpose the page_title variable supports the django
    templating language and will be rendered using the context defined by the
    views get_context_data.
    """

    page_title = ""

    def render_context_with_title(self, context):
        """This function takes in a context dict and uses it to render the
        page_title variable, it then appends this title to the context using
        the 'page_title' key. If there is already a page_title key defined in
        context received then this function will do nothing.
        """

        if "page_title" not in context:
            con = template.Context(context)
            # NOTE(sambetts): Use force_text to ensure lazy translations
            # are handled correctly.
            temp = template.Template(encoding.force_text(self.page_title))
            context["page_title"] = temp.render(con)
        return context

    def render_to_response(self, context):
        """This is an override of the default render_to_response function that
        exists in the django generic views, this is here to inject the
        page title into the context before the main template is rendered.
        """

        context = self.render_context_with_title(context)
        return super(PageTitleMixin, self).render_to_response(context)


class HorizonTemplateView(PageTitleMixin, generic.TemplateView):
    pass


class HorizonFormView(PageTitleMixin, generic.FormView):
    pass


def user_home(request):
    """Reversible named view to direct a user to the appropriate homepage."""
    return shortcuts.redirect(horizon.get_user_home(request.user))


class APIView(HorizonTemplateView):
    """A quick class-based view for putting API data into a template.

    Subclasses must define one method, ``get_data``, and a template name
    via the ``template_name`` attribute on the class.

    Errors within the ``get_data`` function are automatically caught by
    the :func:`horizon.exceptions.handle` error handler if not otherwise
    caught.
    """

    def get_data(self, request, context, *args, **kwargs):
        """This method should handle any necessary API calls, update the
        context object, and return the context object at the end.
        """
        return context

    def get(self, request, *args, **kwargs):
        context = self.get_context_data(**kwargs)
        try:
            context = self.get_data(request, context, *args, **kwargs)
        except Exception:
            exceptions.handle(request)
        return self.render_to_response(context)
