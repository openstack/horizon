# vim: tabstop=4 shiftwidth=4 softtabstop=4

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
from django.views import generic

import horizon
from horizon import exceptions


def user_home(request):
    """ Reversible named view to direct a user to the appropriate homepage. """
    return shortcuts.redirect(horizon.get_user_home(request.user))


class APIView(generic.TemplateView):
    """ A quick class-based view for putting API data into a template.

    Subclasses must define one method, ``get_data``, and a template name
    via the ``template_name`` attribute on the class.

    Errors within the ``get_data`` function are automatically caught by
    the :func:`horizon.exceptions.handle` error handler if not otherwise
    caught.
    """
    def get_data(self, request, context, *args, **kwargs):
        """
        This method should handle any necessary API calls, update the
        context object, and return the context object at the end.
        """
        raise NotImplementedError("You must define a get_data method "
                                   "on %s" % self.__class__.__name__)

    def get(self, request, *args, **kwargs):
        context = self.get_context_data(**kwargs)
        try:
            context = self.get_data(request, context, *args, **kwargs)
        except Exception:
            exceptions.handle(request)
        return self.render_to_response(context)
