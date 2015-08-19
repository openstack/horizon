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

import copy
import json

from django import forms
from django import http
from django import shortcuts
from django.views import generic

import six

from horizon import exceptions
from horizon.forms import views as hz_views
from horizon.forms.views import ADD_TO_FIELD_HEADER  # noqa
from horizon import messages


class WorkflowView(hz_views.ModalBackdropMixin, generic.TemplateView):
    """A generic class-based view which handles the intricacies of workflow
    processing with minimal user configuration.

    .. attribute:: workflow_class

        The :class:`~horizon.workflows.Workflow` class which this view handles.
        Required.

    .. attribute:: template_name

        The template to use when rendering this view via standard HTTP
        requests. Required.

    .. attribute:: ajax_template_name

        The template to use when rendering the workflow for AJAX requests.
        In general the default common template should be used. Defaults to
        ``"horizon/common/_workflow.html"``.

    .. attribute:: context_object_name

        The key which should be used for the workflow object in the template
        context. Defaults to ``"workflow"``.

    """
    workflow_class = None
    template_name = 'horizon/common/_workflow_base.html'
    context_object_name = "workflow"
    ajax_template_name = 'horizon/common/_workflow.html'
    step_errors = {}

    def __init__(self):
        super(WorkflowView, self).__init__()
        if not self.workflow_class:
            raise AttributeError("You must set the workflow_class attribute "
                                 "on %s." % self.__class__.__name__)

    def get_initial(self):
        """Returns initial data for the workflow. Defaults to using the GET
        parameters to allow pre-seeding of the workflow context values.
        """
        return copy.copy(self.request.GET)

    def get_workflow(self):
        """Returns the instantiated workflow class."""
        extra_context = self.get_initial()
        entry_point = self.request.GET.get("step", None)
        workflow = self.workflow_class(self.request,
                                       context_seed=extra_context,
                                       entry_point=entry_point)
        return workflow

    def get_context_data(self, **kwargs):
        """Returns the template context, including the workflow class.

        This method should be overridden in subclasses to provide additional
        context data to the template.
        """
        context = super(WorkflowView, self).get_context_data(**kwargs)
        workflow = self.get_workflow()
        context[self.context_object_name] = workflow
        next = self.request.REQUEST.get(workflow.redirect_param_name, None)
        context['REDIRECT_URL'] = next
        context['layout'] = self.get_layout()
        # For consistency with Workflow class
        context['modal'] = 'modal' in context['layout']

        if ADD_TO_FIELD_HEADER in self.request.META:
            context['add_to_field'] = self.request.META[ADD_TO_FIELD_HEADER]
        return context

    def get_layout(self):
        """returns classes for the workflow element in template based on
        the workflow characteristics
        """
        if self.request.is_ajax():
            layout = ['modal', ]
            if self.workflow_class.fullscreen:
                layout += ['fullscreen', ]
        else:
            layout = ['static_page', ]

        if self.workflow_class.wizard:
            layout += ['wizard', ]

        return layout

    def get_template_names(self):
        """Returns the template name to use for this request."""
        if self.request.is_ajax():
            template = self.ajax_template_name
        else:
            template = self.template_name
        return template

    def get_object_id(self, obj):
        return getattr(obj, "id", None)

    def get_object_display(self, obj):
        return getattr(obj, "name", None)

    def add_error_to_step(self, error_msg, step):
        self.step_errors[step] = error_msg

    def set_workflow_step_errors(self, context):
        workflow = context['workflow']
        for step in self.step_errors:
            error_msg = self.step_errors[step]
            workflow.add_error_to_step(error_msg, step)

    def get(self, request, *args, **kwargs):
        """Handler for HTTP GET requests."""
        context = self.get_context_data(**kwargs)
        self.set_workflow_step_errors(context)
        return self.render_to_response(context)

    def validate_steps(self, request, workflow, start, end):
        """Validates the workflow steps from ``start`` to ``end``, inclusive.

        Returns a dict describing the validation state of the workflow.
        """
        errors = {}
        for step in workflow.steps[start:end + 1]:
            if not step.action.is_valid():
                errors[step.slug] = dict(
                    (field, [six.text_type(error) for error in errors])
                    for (field, errors) in six.iteritems(step.action.errors))
        return {
            'has_errors': bool(errors),
            'workflow_slug': workflow.slug,
            'errors': errors,
        }

    def post(self, request, *args, **kwargs):
        """Handler for HTTP POST requests."""
        context = self.get_context_data(**kwargs)
        workflow = context[self.context_object_name]
        try:
            # Check for the VALIDATE_STEP* headers, if they are present
            # and valid integers, return validation results as JSON,
            # otherwise proceed normally.
            validate_step_start = int(self.request.META.get(
                'HTTP_X_HORIZON_VALIDATE_STEP_START', ''))
            validate_step_end = int(self.request.META.get(
                'HTTP_X_HORIZON_VALIDATE_STEP_END', ''))
        except ValueError:
            # No VALIDATE_STEP* headers, or invalid values. Just proceed
            # with normal workflow handling for POSTs.
            pass
        else:
            # There are valid VALIDATE_STEP* headers, so only do validation
            # for the specified steps and return results.
            data = self.validate_steps(request, workflow,
                                       validate_step_start,
                                       validate_step_end)
            return http.HttpResponse(json.dumps(data),
                                     content_type="application/json")
        if not workflow.is_valid():
            return self.render_to_response(context)
        try:
            success = workflow.finalize()
        except forms.ValidationError:
            return self.render_to_response(context)
        except Exception:
            success = False
            exceptions.handle(request)
        if success:
            msg = workflow.format_status_message(workflow.success_message)
            messages.success(request, msg)
        else:
            msg = workflow.format_status_message(workflow.failure_message)
            messages.error(request, msg)
        if "HTTP_X_HORIZON_ADD_TO_FIELD" in self.request.META:
            field_id = self.request.META["HTTP_X_HORIZON_ADD_TO_FIELD"]
            response = http.HttpResponse()
            if workflow.object:
                data = [self.get_object_id(workflow.object),
                        self.get_object_display(workflow.object)]
                response.content = json.dumps(data)
                response["X-Horizon-Add-To-Field"] = field_id
            return response
        next_url = self.request.REQUEST.get(workflow.redirect_param_name, None)
        return shortcuts.redirect(next_url or workflow.get_success_url())
