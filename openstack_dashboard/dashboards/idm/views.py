# Copyright (C) 2014 Universidad Politecnica de Madrid
#
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

from django.views.generic.base import TemplateResponseMixin, ContextMixin, View
from django.http import HttpResponseRedirect

from horizon.utils import memoized

from openstack_dashboard.dashboards.idm import utils


class MultiFormMixin(ContextMixin):
    """Similiar behaviour of django's FormMixin but for multiple forms on display."""
    initals = {}
    forms_classes = []
    prefixes = {}
    endpoints = {}
    form_to_handle_class = None
    success_url = None

    def __new__(cls, name, bases, attrs):
        """Check basic stuff to avoid hard to find errors."""
        form_to_handle_class = attrs.get('form_to_handle_class')
        forms_classes = attrs.get('forms_classes')
        if form_to_handle_class not in forms_classes:
            raise TypeError('The form to be handle has to be in the forms_classes list')
        for attr in ['initals', 'prefixes', 'endpoints']:
            utils.check_elements(attrs.get(attr).keys(), forms_classes)      
        return super(MultiFormMixin, cls).__new__(cls, name, bases, attrs)

    def get_initial(self, form_class):
        """Retrieve initial data for the form. By default, returns a copy of initial."""
        return self.initial.get(form_class).copy()

    def get_endpoint(self, form_class):
        """Retrieve the form handling endpoint view."""
        return self.endpoints.get(form_class)

    def get_forms_classes(self):
        """Retrieve the form class to instantiate. By default forms_classes."""
        return self.forms_classes

    def _get_form(self, form_class):
        """Returns an instance of a form"""
        form = form_class(**self.get_form_kwargs(form_class))
        form.action = self.get_endpoint(form_class)
        return form

    def get_forms(self, handled_form=None):
        """Returns an instance of every form to be used in this view and replaces 
        the handled one if present to show the errors."""
        return [handled_form if isinstance(handled_form, form_class) 
                    else self._get_form(form_class) 
                    for form_class in self.get_forms_classes()]

    def get_form_kwargs(self, form_class):
        """Returns the keyword arguments for instantiating the form."""
        kwargs = {
            'initial': self.get_initial(form_class),
            'prefix': self.get_prefix(form_class),
        }
        return kwargs

    def get_prefix(self, form_class):
        """Returns the prefix to use for forms on this view."""
        return self.prefix.get(form_class)

    def form_valid(self, form):
        """If the form is valid, redirect to the supplied URL."""
        return HttpResponseRedirect(self.get_success_url())

    def form_invalid(self, form):
        """If the form is invalid, re-render the context data with the
        data-filled form and errors.
        """
        return self.render_to_response(self.get_context_data(handled_form=form))

    def get_form_to_handle(self):
        """Returns an instance of the form to be handled in this view."""
        return self._get_form(self.form_to_handle_class)

    def get_context_data(self, **kwargs):
        """Instantiates the forms."""
        context = super(MultiFormMixin, self).get_context_data(**kwargs)
        context['forms'] = self.get_forms(handled_form=kwargs.get('handled_form', None))
        return context


class BaseMultiFormView(MultiFormMixin, TemplateResponseMixin, View):
    """View to display of multiple forms on a single page and handle the post
    of one of those forms. Heavily inspired by django's ProcessFormView.

    This view renders several forms. Each form should post to a different endpoint
    for validation and handling. These endpoints can be regular FormViews (or any other 
    view able to handle a from like horizon's ModalFormView) or MultiFormViews. If 
    you want to support the use case of showing form errors in the multiple form page
    the endpoints have to be MultiFormViews.

    The general usage is to inherit this base class with your own base and then 
    inherit your base class for every view, to avoid repeting the common parts.
    """

    def get(self, request, *args, **kwargs):
        """Handles GET requests"""
        self.object = self.get_object()
        return self.render_to_response(self.get_context_data())

    def post(self, request, *args, **kwargs):
        """Handles POST requests, instantiating a form instance with the passed
        POST variables and then checked for validity.
        """
        form = self.get_form_to_handle()
        if form.is_valid():
            return self.form_valid(form)
        else:
            return self.form_invalid(form)

    def update_initials(self):
        """Execution-time initial values for the forms. """
        pass

    @memoized.memoized_method
    def get_object(self):
        """API calls to get the main object to edit.

        :returns: the object, for example a project.

        """
        raise NotImplementedError() 