# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright 2011 Nebula, Inc.
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

import os

from django.views import generic


class ModalFormView(generic.TemplateView):
    form_class = None
    initial = {}
    context_form_name = "form"
    context_object_name = "object"

    def get_template_names(self):
        if self.request.is_ajax():
            if not hasattr(self, "ajax_template_name"):
                # Transform standard template name to ajax name (leading "_")
                bits = list(os.path.split(self.template_name))
                bits[1] = "".join(("_", bits[1]))
                self.ajax_template_name = os.path.join(*bits)
            template = self.ajax_template_name
        else:
            template = self.template_name
        return template

    def get_object(self, *args, **kwargs):
        return None

    def get_initial(self):
        return self.initial

    def get_form_kwargs(self):
        kwargs = {'initial': self.get_initial()}
        return kwargs

    def maybe_handle(self):
        if not self.form_class:
            raise AttributeError('You must specify a SelfHandlingForm class '
                                 'for the "form_class" attribute on %s.'
                                 % self.__class__.__name__)
        if not hasattr(self, "form"):
            form = self.form_class
            kwargs = self.get_form_kwargs()
            self.form, self.handled = form.maybe_handle(self.request, **kwargs)
        return self.form, self.handled

    def get(self, request, *args, **kwargs):
        self.object = self.get_object(*args, **kwargs)
        form, handled = self.maybe_handle()
        if handled:
            return handled
        context = self.get_context_data(**kwargs)
        context[self.context_form_name] = form
        context[self.context_object_name] = self.object
        if self.request.is_ajax():
            context['hide'] = True
        return self.render_to_response(context)

    def post(self, request, *args, **kwargs):
        """ Placeholder to allow POST; handled the same as GET. """
        return self.get(self, request, *args, **kwargs)
