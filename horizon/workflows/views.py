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

import copy

from django import shortcuts
from django.contrib import messages
from django.views import generic

from horizon import exceptions


class WorkflowView(generic.TemplateView):
    """
    A generic class-based view which handles the intricacies of workflow
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
    template_name = None
    context_object_name = "workflow"
    ajax_template_name = 'horizon/common/_workflow.html'

    def __init__(self):
        if not self.workflow_class:
            raise AttributeError("You must set the workflow_class attribute "
                                 "on %s." % self.__class__.__name__)

    def get_initial(self):
        """
        Returns initial data for the workflow. Defaults to using the GET
        parameters to allow pre-seeding of the workflow context values.
        """
        return copy.copy(self.request.GET)

    def get_workflow(self):
        """ Returns the instanciated workflow class. """
        extra_context = self.get_initial()
        workflow = self.workflow_class(self.request,
                                       context_seed=extra_context)
        return workflow

    def get_context_data(self, **kwargs):
        """
        Returns the template context, including the workflow class.

        This method should be overridden in subclasses to provide additional
        context data to the template.
        """
        context = super(WorkflowView, self).get_context_data(**kwargs)
        context[self.context_object_name] = self.get_workflow()
        if self.request.is_ajax():
            context['modal'] = True
        return context

    def get_template_names(self):
        """ Returns the template name to use for this request. """
        if self.request.is_ajax():
            template = self.ajax_template_name
        else:
            template = self.template_name
        return template

    def get(self, request, *args, **kwargs):
        """ Handler for HTTP GET requests. """
        context = self.get_context_data(**kwargs)
        return self.render_to_response(context)

    def post(self, request, *args, **kwargs):
        """ Handler for HTTP POST requests. """
        context = self.get_context_data(**kwargs)
        workflow = context[self.context_object_name]
        if workflow.is_valid():
            try:
                success = workflow.finalize()
            except:
                success = False
                exceptions.handle(request)
            if success:
                msg = workflow.format_status_message(workflow.success_message)
                messages.success(request, msg)
                return shortcuts.redirect(workflow.get_success_url())
            else:
                msg = workflow.format_status_message(workflow.failure_message)
                messages.error(request, msg)
                return shortcuts.redirect(workflow.get_success_url())
        else:
            return self.render_to_response(context)
