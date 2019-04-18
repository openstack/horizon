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

import json
import os

from django.conf import settings
from django import http
from django.utils.translation import ugettext_lazy as _

from horizon import exceptions
from horizon import views


ADD_TO_FIELD_HEADER = "HTTP_X_HORIZON_ADD_TO_FIELD"


class ModalBackdropMixin(object):
    """Mixin class to allow ModalFormView and WorkflowView together.

    This mixin class is to be used for together with ModalFormView and
    WorkflowView classes to augment them with modal_backdrop context data.

    .. attribute: modal_backdrop (optional)

        The appearance and behavior of backdrop under the modal element.
        Possible options are:
        * 'true' - show backdrop element outside the modal, close the modal
        after clicking on backdrop (the default one);
        * 'false' - do not show backdrop element, do not close the modal after
        clicking outside of it;
        * 'static' - show backdrop element outside the modal, do not close
        the modal after clicking on backdrop.
    """
    modal_backdrop = 'static'

    def __init__(self, *args, **kwargs):
        super(ModalBackdropMixin, self).__init__(*args, **kwargs)
        config = settings.HORIZON_CONFIG
        if 'modal_backdrop' in config:
            self.modal_backdrop = config['modal_backdrop']

    def get_context_data(self, **kwargs):
        context = super(ModalBackdropMixin, self).get_context_data(**kwargs)
        context['modal_backdrop'] = self.modal_backdrop
        return context


class ModalFormMixin(ModalBackdropMixin):
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

    def get_context_data(self, **kwargs):
        context = super(ModalFormMixin, self).get_context_data(**kwargs)
        if self.request.is_ajax():
            context['hide'] = True
        if ADD_TO_FIELD_HEADER in self.request.META:
            context['add_to_field'] = self.request.META[ADD_TO_FIELD_HEADER]
        return context


class ModalFormView(ModalFormMixin, views.HorizonFormView):
    """The main view class for all views which handle forms in Horizon.

    All view which handles forms in Horiozn should inherit this class.
    It takes care of all details with processing
    :class:`~horizon.forms.base.SelfHandlingForm` classes, and modal concerns
    when the associated template inherits from
    `horizon/common/_modal_form.html`.

    Subclasses must define a ``form_class`` and ``template_name`` attribute
    at minimum.

    See Django's documentation on the `FormView <https://docs.djangoproject.com
    /en/dev/ref/class-based-views/generic-editing/#formview>`_ class for
    more details.

    .. attribute: modal_id (recommended)

        The HTML element id of this modal.

    .. attribute: modal_header (recommended)

        The title of this modal.

    .. attribute: form_id (recommended)

        The HTML element id of the form in this modal.

    .. attribute: submit_url (required)

        The url for a submit action.

    .. attribute: submit_label (optional)

        The label for the submit button. This label defaults to ``Submit``.
        This button should only be visible if the action_url is defined.
        Clicking on this button will post to the action_url.

    .. attribute: cancel_label (optional)

        The label for the cancel button. This label defaults to ``Cancel``.
        Clicking on this button will redirect user to the cancel_url.

    .. attribute: cancel_url (optional)

        The url for a cancel action. This url defaults to the success_url
        if omitted. Note that the cancel_url redirect is nullified when
        shown in a modal dialog.
    """

    modal_id = None
    modal_header = ""
    form_id = None
    submit_url = None
    submit_label = _("Submit")
    cancel_label = _("Cancel")
    cancel_url = None

    def get_context_data(self, **kwargs):
        context = super(ModalFormView, self).get_context_data(**kwargs)
        context['modal_id'] = self.modal_id
        context['modal_header'] = self.modal_header
        context['form_id'] = self.form_id
        context['submit_url'] = self.submit_url
        context['submit_label'] = self.submit_label
        context['cancel_label'] = self.cancel_label
        context['cancel_url'] = self.get_cancel_url()
        return context

    def get_cancel_url(self):
        return self.cancel_url or self.success_url

    def get_object_id(self, obj):
        """Returns the ID of the created object.

        For  dynamic insertion of resources created in modals,
        this method returns the id of the created object.
        Defaults to returning the ``id`` attribute.
        """
        return obj.id

    def get_object_display(self, obj):
        """Returns the display name of the created object.

        For dynamic insertion of resources created in modals,
        this method returns the display name of the created object.
        Defaults to returning the ``name`` attribute.
        """
        return obj.name

    def get_form(self, form_class=None):
        """Returns an instance of the form to be used in this view."""
        if form_class is None:
            form_class = self.get_form_class()
        return form_class(self.request, **self.get_form_kwargs())

    def form_invalid(self, form):
        context = self.get_context_data()
        context['form'] = form
        return self.render_to_response(context)

    def form_valid(self, form):
        try:
            handled = form.handle(self.request, form.cleaned_data)
        except Exception:
            handled = None
            exceptions.handle(self.request)

        if handled:
            if ADD_TO_FIELD_HEADER in self.request.META:
                field_id = self.request.META[ADD_TO_FIELD_HEADER]
                data = [self.get_object_id(handled),
                        self.get_object_display(handled)]
                response = http.HttpResponse(
                    json.dumps(data), content_type="text/plain")
                response["X-Horizon-Add-To-Field"] = field_id
            elif isinstance(handled, http.HttpResponse):
                return handled
            else:
                try:
                    success_url = self.get_success_url_from_handled(handled)
                except AttributeError:
                    success_url = self.get_success_url()

                response = http.HttpResponseRedirect(success_url)
                if hasattr(handled, 'to_dict'):
                    obj_dict = handled.to_dict()
                    if 'upload_url' in obj_dict:
                        response['X-File-Upload-URL'] = obj_dict['upload_url']
                        response['X-Auth-Token'] = obj_dict['token_id']
                # TODO(gabriel): This is not a long-term solution to how
                # AJAX should be handled, but it's an expedient solution
                # until the blueprint for AJAX handling is architected
                # and implemented.
                response['X-Horizon-Location'] = success_url
            return response
        else:
            # If handled didn't return, we can assume something went
            # wrong, and we should send back the form as-is.
            return self.form_invalid(form)
