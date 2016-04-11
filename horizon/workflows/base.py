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
import inspect
import logging

from django.core import urlresolvers
from django import forms
from django.forms.forms import NON_FIELD_ERRORS  # noqa
from django import template
from django.template.defaultfilters import linebreaks  # noqa
from django.template.defaultfilters import safe  # noqa
from django.template.defaultfilters import slugify  # noqa
from django.utils.encoding import force_text
from django.utils.translation import ugettext_lazy as _
from importlib import import_module
import six

from horizon import base
from horizon import exceptions
from horizon.templatetags.horizon import has_permissions  # noqa
from horizon.utils import html


LOG = logging.getLogger(__name__)


class WorkflowContext(dict):
    def __init__(self, workflow, *args, **kwargs):
        super(WorkflowContext, self).__init__(*args, **kwargs)
        self._workflow = workflow

    def __setitem__(self, key, val):
        super(WorkflowContext, self).__setitem__(key, val)
        return self._workflow._trigger_handlers(key)

    def __delitem__(self, key):
        return self.__setitem__(key, None)

    def set(self, key, val):
        return self.__setitem__(key, val)

    def unset(self, key):
        return self.__delitem__(key)


class ActionMetaclass(forms.forms.DeclarativeFieldsMetaclass):
    def __new__(mcs, name, bases, attrs):
        # Pop Meta for later processing
        opts = attrs.pop("Meta", None)
        # Create our new class
        cls = super(ActionMetaclass, mcs).__new__(mcs, name, bases, attrs)
        # Process options from Meta
        cls.name = getattr(opts, "name", name)
        cls.slug = getattr(opts, "slug", slugify(name))
        cls.permissions = getattr(opts, "permissions", ())
        cls.progress_message = getattr(opts,
                                       "progress_message",
                                       _("Processing..."))
        cls.help_text = getattr(opts, "help_text", "")
        cls.help_text_template = getattr(opts, "help_text_template", None)
        return cls


@six.python_2_unicode_compatible
@six.add_metaclass(ActionMetaclass)
class Action(forms.Form):
    """An ``Action`` represents an atomic logical interaction you can have with
    the system. This is easier to understand with a conceptual example: in the
    context of a "launch instance" workflow, actions would include "naming
    the instance", "selecting an image", and ultimately "launching the
    instance".

    Because ``Actions`` are always interactive, they always provide form
    controls, and thus inherit from Django's ``Form`` class. However, they
    have some additional intelligence added to them:

    * ``Actions`` are aware of the permissions required to complete them.

    * ``Actions`` have a meta-level concept of "help text" which is meant to be
      displayed in such a way as to give context to the action regardless of
      where the action is presented in a site or workflow.

    * ``Actions`` understand how to handle their inputs and produce outputs,
      much like :class:`~horizon.forms.SelfHandlingForm` does now.

    ``Action`` classes may define the following attributes in a ``Meta``
    class within them:

    .. attribute:: name

        The verbose name for this action. Defaults to the name of the class.

    .. attribute:: slug

        A semi-unique slug for this action. Defaults to the "slugified" name
        of the class.

    .. attribute:: permissions

        A list of permission names which this action requires in order to be
        completed. Defaults to an empty list (``[]``).

    .. attribute:: help_text

        A string of simple help text to be displayed alongside the Action's
        fields.

    .. attribute:: help_text_template

        A path to a template which contains more complex help text to be
        displayed alongside the Action's fields. In conjunction with
        :meth:`~horizon.workflows.Action.get_help_text` method you can
        customize your help text template to display practically anything.
    """

    def __init__(self, request, context, *args, **kwargs):
        if request.method == "POST":
            super(Action, self).__init__(request.POST, initial=context)
        else:
            super(Action, self).__init__(initial=context)

        if not hasattr(self, "handle"):
            raise AttributeError("The action %s must define a handle method."
                                 % self.__class__.__name__)
        self.request = request
        self._populate_choices(request, context)
        self.required_css_class = 'required'

    def __str__(self):
        return force_text(self.name)

    def __repr__(self):
        return "<%s: %s>" % (self.__class__.__name__, self.slug)

    def _populate_choices(self, request, context):
        for field_name, bound_field in self.fields.items():
            meth = getattr(self, "populate_%s_choices" % field_name, None)
            if meth is not None and callable(meth):
                bound_field.choices = meth(request, context)

    def get_help_text(self, extra_context=None):
        """Returns the help text for this step."""
        text = ""
        extra_context = extra_context or {}
        if self.help_text_template:
            tmpl = template.loader.get_template(self.help_text_template)
            context = template.RequestContext(self.request, extra_context)
            text += tmpl.render(context)
        else:
            text += linebreaks(force_text(self.help_text))
        return safe(text)

    def add_action_error(self, message):
        """Adds an error to the Action's Step based on API issues."""
        self.errors[NON_FIELD_ERRORS] = self.error_class([message])

    def handle(self, request, context):
        """Handles any requisite processing for this action. The method should
        return either ``None`` or a dictionary of data to be passed to
        :meth:`~horizon.workflows.Step.contribute`.

        Returns ``None`` by default, effectively making it a no-op.
        """
        return None


class MembershipAction(Action):
    """An action that allows a user to add/remove members from a group.

    Extend the Action class with additional helper method for membership
    management.
    """
    def get_default_role_field_name(self):
        return "default_" + self.slug + "_role"

    def get_member_field_name(self, role_id):
        return self.slug + "_role_" + role_id


@six.python_2_unicode_compatible
class Step(object):
    """A step is a wrapper around an action which defines its context in a
    workflow. It knows about details such as:

    * The workflow's context data (data passed from step to step).

    * The data which must be present in the context to begin this step (the
      step's dependencies).

    * The keys which will be added to the context data upon completion of the
      step.

    * The connections between this step's fields and changes in the context
      data (e.g. if that piece of data changes, what needs to be updated in
      this step).

    A ``Step`` class has the following attributes:

    .. attribute:: action_class

        The :class:`~horizon.workflows.Action` class which this step wraps.

    .. attribute:: depends_on

        A list of context data keys which this step requires in order to
        begin interaction.

    .. attribute:: contributes

        A list of keys which this step will contribute to the workflow's
        context data. Optional keys should still be listed, even if their
        values may be set to ``None``.

    .. attribute:: connections

        A dictionary which maps context data key names to lists of callbacks.
        The callbacks may be functions, dotted python paths to functions
        which may be imported, or dotted strings beginning with ``"self"``
        to indicate methods on the current ``Step`` instance.

    .. attribute:: before

        Another ``Step`` class. This optional attribute is used to provide
        control over workflow ordering when steps are dynamically added to
        workflows. The workflow mechanism will attempt to place the current
        step before the step specified in the attribute.

    .. attribute:: after

        Another ``Step`` class. This attribute has the same purpose as
        :meth:`~horizon.workflows.Step.before` except that it will instead
        attempt to place the current step after the given step.

    .. attribute:: help_text

        A string of simple help text which will be prepended to the ``Action``
        class' help text if desired.

    .. attribute:: template_name

        A path to a template which will be used to render this step. In
        general the default common template should be used. Default:
        ``"horizon/common/_workflow_step.html"``.

    .. attribute:: has_errors

        A boolean value which indicates whether or not this step has any
        errors on the action within it or in the scope of the workflow. This
        attribute will only accurately reflect this status after validation
        has occurred.

    .. attribute:: slug

        Inherited from the ``Action`` class.

    .. attribute:: name

        Inherited from the ``Action`` class.

    .. attribute:: permissions

        Inherited from the ``Action`` class.
    """
    action_class = None
    depends_on = ()
    contributes = ()
    connections = None
    before = None
    after = None
    help_text = ""
    template_name = "horizon/common/_workflow_step.html"

    def __repr__(self):
        return "<%s: %s>" % (self.__class__.__name__, self.slug)

    def __str__(self):
        return force_text(self.name)

    def __init__(self, workflow):
        super(Step, self).__init__()
        self.workflow = workflow

        cls = self.__class__.__name__
        if not (self.action_class and issubclass(self.action_class, Action)):
            raise AttributeError("action_class not specified for %s." % cls)

        self.slug = self.action_class.slug
        self.name = self.action_class.name
        self.permissions = self.action_class.permissions
        self.has_errors = False
        self._handlers = {}

        if self.connections is None:
            # We want a dict, but don't want to declare a mutable type on the
            # class directly.
            self.connections = {}

        # Gather our connection handlers and make sure they exist.
        for key, handlers in self.connections.items():
            self._handlers[key] = []
            # TODO(gabriel): This is a poor substitute for broader handling
            if not isinstance(handlers, (list, tuple)):
                raise TypeError("The connection handlers for %s must be a "
                                "list or tuple." % cls)
            for possible_handler in handlers:
                if callable(possible_handler):
                    # If it's callable we know the function exists and is valid
                    self._handlers[key].append(possible_handler)
                    continue
                elif not isinstance(possible_handler, six.string_types):
                    raise TypeError("Connection handlers must be either "
                                    "callables or strings.")
                bits = possible_handler.split(".")
                if bits[0] == "self":
                    root = self
                    for bit in bits[1:]:
                        try:
                            root = getattr(root, bit)
                        except AttributeError:
                            raise AttributeError("The connection handler %s "
                                                 "could not be found on %s."
                                                 % (possible_handler, cls))
                    handler = root
                elif len(bits) == 1:
                    # Import by name from local module not supported
                    raise ValueError("Importing a local function as a string "
                                     "is not supported for the connection "
                                     "handler %s on %s."
                                     % (possible_handler, cls))
                else:
                    # Try a general import
                    module_name = ".".join(bits[:-1])
                    try:
                        mod = import_module(module_name)
                        handler = getattr(mod, bits[-1])
                    except ImportError:
                        raise ImportError("Could not import %s from the "
                                          "module %s as a connection "
                                          "handler on %s."
                                          % (bits[-1], module_name, cls))
                    except AttributeError:
                        raise AttributeError("Could not import %s from the "
                                             "module %s as a connection "
                                             "handler on %s."
                                             % (bits[-1], module_name, cls))
                self._handlers[key].append(handler)

    @property
    def action(self):
        if not getattr(self, "_action", None):
            try:
                # Hook in the action context customization.
                workflow_context = dict(self.workflow.context)
                context = self.prepare_action_context(self.workflow.request,
                                                      workflow_context)
                self._action = self.action_class(self.workflow.request,
                                                 context)
            except Exception:
                LOG.exception("Problem instantiating action class.")
                raise
        return self._action

    def prepare_action_context(self, request, context):
        """Allows for customization of how the workflow context is passed to
        the action; this is the reverse of what "contribute" does to make the
        action outputs sane for the workflow. Changes to the context are not
        saved globally here. They are localized to the action.

        Simply returns the unaltered context by default.
        """
        return context

    def get_id(self):
        """Returns the ID for this step. Suitable for use in HTML markup."""
        return "%s__%s" % (self.workflow.slug, self.slug)

    def _verify_contributions(self, context):
        for key in self.contributes:
            # Make sure we don't skip steps based on weird behavior of
            # POST query dicts.
            field = self.action.fields.get(key, None)
            if field and field.required and not context.get(key):
                context.pop(key, None)
        failed_to_contribute = set(self.contributes)
        failed_to_contribute -= set(context.keys())
        if failed_to_contribute:
            raise exceptions.WorkflowError("The following expected data was "
                                           "not added to the workflow context "
                                           "by the step %s: %s."
                                           % (self.__class__,
                                              failed_to_contribute))
        return True

    def contribute(self, data, context):
        """Adds the data listed in ``contributes`` to the workflow's shared
        context. By default, the context is simply updated with all the data
        returned by the action.

        Note that even if the value of one of the ``contributes`` keys is
        not present (e.g. optional) the key should still be added to the
        context with a value of ``None``.
        """
        if data:
            for key in self.contributes:
                context[key] = data.get(key, None)
        return context

    def render(self):
        """Renders the step."""
        step_template = template.loader.get_template(self.template_name)
        extra_context = {"form": self.action,
                         "step": self}
        context = template.RequestContext(self.workflow.request, extra_context)
        return step_template.render(context)

    def get_help_text(self):
        """Returns the help text for this step."""
        text = linebreaks(force_text(self.help_text))
        text += self.action.get_help_text()
        return safe(text)

    def add_step_error(self, message):
        """Adds an error to the Step based on API issues."""
        self.action.add_action_error(message)

    def has_required_fields(self):
        """Returns True if action contains any required fields."""
        return any(field.required for field in self.action.fields.values())


class WorkflowMetaclass(type):
    def __new__(mcs, name, bases, attrs):
        super(WorkflowMetaclass, mcs).__new__(mcs, name, bases, attrs)
        attrs["_cls_registry"] = set([])
        return type.__new__(mcs, name, bases, attrs)


class UpdateMembersStep(Step):
    """A step that allows a user to add/remove members from a group.

    .. attribute:: show_roles

        Set to False to disable the display of the roles dropdown.

    .. attribute:: available_list_title

        The title used for the available list column.

    .. attribute:: members_list_title

        The title used for the members list column.

    .. attribute:: no_available_text

        The placeholder text used when the available list is empty.

    .. attribute:: no_members_text

        The placeholder text used when the members list is empty.

    """
    template_name = "horizon/common/_workflow_step_update_members.html"
    show_roles = True
    available_list_title = _("All available")
    members_list_title = _("Members")
    no_available_text = _("None available.")
    no_members_text = _("No members.")

    def get_member_field_name(self, role_id):
        if issubclass(self.action_class, MembershipAction):
            return self.action.get_member_field_name(role_id)
        else:
            return self.slug + "_role_" + role_id


@six.python_2_unicode_compatible
@six.add_metaclass(WorkflowMetaclass)
class Workflow(html.HTMLElement):
    """A Workflow is a collection of Steps. Its interface is very
    straightforward, but it is responsible for handling some very
    important tasks such as:

    * Handling the injection, removal, and ordering of arbitrary steps.

    * Determining if the workflow can be completed by a given user at runtime
      based on all available information.

    * Dispatching connections between steps to ensure that when context data
      changes all the applicable callback functions are executed.

    * Verifying/validating the overall data integrity and subsequently
      triggering the final method to complete the workflow.

    The ``Workflow`` class has the following attributes:

    .. attribute:: name

        The verbose name for this workflow which will be displayed to the user.
        Defaults to the class name.

    .. attribute:: slug

        The unique slug for this workflow. Required.

    .. attribute:: steps

        Read-only access to the final ordered set of step instances for
        this workflow.

    .. attribute:: default_steps

        A list of :class:`~horizon.workflows.Step` classes which serve as the
        starting point for this workflow's ordered steps. Defaults to an empty
        list (``[]``).

    .. attribute:: finalize_button_name

        The name which will appear on the submit button for the workflow's
        form. Defaults to ``"Save"``.

    .. attribute:: success_message

        A string which will be displayed to the user upon successful completion
        of the workflow. Defaults to
        ``"{{ workflow.name }} completed successfully."``

    .. attribute:: failure_message

        A string which will be displayed to the user upon failure to complete
        the workflow. Defaults to ``"{{ workflow.name }} did not complete."``

    .. attribute:: depends_on

        A roll-up list of all the ``depends_on`` values compiled from the
        workflow's steps.

    .. attribute:: contributions

        A roll-up list of all the ``contributes`` values compiled from the
        workflow's steps.

    .. attribute:: template_name

        Path to the template which should be used to render this workflow.
        In general the default common template should be used. Default:
        ``"horizon/common/_workflow.html"``.

    .. attribute:: entry_point

        The slug of the step which should initially be active when the
        workflow is rendered. This can be passed in upon initialization of
        the workflow, or set anytime after initialization but before calling
        either ``get_entry_point`` or ``render``.

    .. attribute:: redirect_param_name

        The name of a parameter used for tracking the URL to redirect to upon
        completion of the workflow. Defaults to ``"next"``.

    .. attribute:: object

        The object (if any) which this workflow relates to. In the case of
        a workflow which creates a new resource the object would be the created
        resource after the relevant creation steps have been undertaken. In
        the case of a workflow which updates a resource it would be the
        resource being updated after it has been retrieved.

    .. attribute:: wizard

        Whether to present the workflow as a wizard, with "prev" and "next"
        buttons and validation after every step.

    .. attribute:: fullscreen

        If the workflow is presented in a modal, and this attribute is
        set to True, then the ``fullscreen`` css class will be added so
        the modal can take advantage of the available screen estate.
        Defaults to ``False``.

    """
    slug = None
    default_steps = ()
    template_name = "horizon/common/_workflow.html"
    finalize_button_name = _("Save")
    success_message = _("%s completed successfully.")
    failure_message = _("%s did not complete.")
    redirect_param_name = "next"
    multipart = False
    wizard = False
    fullscreen = False
    _registerable_class = Step

    def __str__(self):
        return self.name

    def __repr__(self):
        return "<%s: %s>" % (self.__class__.__name__, self.slug)

    def __init__(self, request=None, context_seed=None, entry_point=None,
                 *args, **kwargs):
        super(Workflow, self).__init__(*args, **kwargs)
        if self.slug is None:
            raise AttributeError("The workflow %s must have a slug."
                                 % self.__class__.__name__)
        self.name = getattr(self, "name", self.__class__.__name__)
        self.request = request
        self.depends_on = set([])
        self.contributions = set([])
        self.entry_point = entry_point
        self.object = None

        # Put together our steps in order. Note that we pre-register
        # non-default steps so that we can identify them and subsequently
        # insert them in order correctly.
        self._registry = dict([(step_class, step_class(self)) for step_class
                               in self.__class__._cls_registry
                               if step_class not in self.default_steps])
        self._gather_steps()

        # Determine all the context data we need to end up with.
        for step in self.steps:
            self.depends_on = self.depends_on | set(step.depends_on)
            self.contributions = self.contributions | set(step.contributes)

        # Initialize our context. For ease we can preseed it with a
        # regular dictionary. This should happen after steps have been
        # registered and ordered.
        self.context = WorkflowContext(self)
        context_seed = context_seed or {}
        clean_seed = dict([(key, val)
                           for key, val in context_seed.items()
                           if key in self.contributions | self.depends_on])
        self.context_seed = clean_seed
        self.context.update(clean_seed)

        if request and request.method == "POST":
            for step in self.steps:
                valid = step.action.is_valid()
                # Be sure to use the CLEANED data if the workflow is valid.
                if valid:
                    data = step.action.cleaned_data
                else:
                    data = request.POST
                self.context = step.contribute(data, self.context)

    @property
    def steps(self):
        if getattr(self, "_ordered_steps", None) is None:
            self._gather_steps()
        return self._ordered_steps

    def get_step(self, slug):
        """Returns the instantiated step matching the given slug."""
        for step in self.steps:
            if step.slug == slug:
                return step

    def _gather_steps(self):
        ordered_step_classes = self._order_steps()
        for default_step in self.default_steps:
            self.register(default_step)
            self._registry[default_step] = default_step(self)
        self._ordered_steps = [self._registry[step_class]
                               for step_class in ordered_step_classes
                               if has_permissions(self.request.user,
                                                  self._registry[step_class])]

    def _order_steps(self):
        steps = list(copy.copy(self.default_steps))
        additional = self._registry.keys()
        for step in additional:
            try:
                min_pos = steps.index(step.after)
            except ValueError:
                min_pos = 0
            try:
                max_pos = steps.index(step.before)
            except ValueError:
                max_pos = len(steps)
            if min_pos > max_pos:
                raise exceptions.WorkflowError("The step %(new)s can't be "
                                               "placed between the steps "
                                               "%(after)s and %(before)s; the "
                                               "step %(before)s comes before "
                                               "%(after)s."
                                               % {"new": additional,
                                                  "after": step.after,
                                                  "before": step.before})
            steps.insert(max_pos, step)
        return steps

    def get_entry_point(self):
        """Returns the slug of the step which the workflow should begin on.

        This method takes into account both already-available data and errors
        within the steps.
        """
        # If we have a valid specified entry point, use it.
        if self.entry_point:
            if self.get_step(self.entry_point):
                return self.entry_point
        # Otherwise fall back to calculating the appropriate entry point.
        for step in self.steps:
            if step.has_errors:
                return step.slug
            try:
                step._verify_contributions(self.context)
            except exceptions.WorkflowError:
                return step.slug
        # If nothing else, just return the first step.
        return self.steps[0].slug

    def _trigger_handlers(self, key):
        responses = []
        handlers = [(step.slug, f) for step in self.steps
                    for f in step._handlers.get(key, [])]
        for slug, handler in handlers:
            responses.append((slug, handler(self.request, self.context)))
        return responses

    @classmethod
    def register(cls, step_class):
        """Registers a :class:`~horizon.workflows.Step` with the workflow."""
        if not inspect.isclass(step_class):
            raise ValueError('Only classes may be registered.')
        elif not issubclass(step_class, cls._registerable_class):
            raise ValueError('Only %s classes or subclasses may be registered.'
                             % cls._registerable_class.__name__)
        if step_class in cls._cls_registry:
            return False
        else:
            cls._cls_registry.add(step_class)
            return True

    @classmethod
    def unregister(cls, step_class):
        """Unregisters a :class:`~horizon.workflows.Step` from the workflow.
        """
        try:
            cls._cls_registry.remove(step_class)
        except KeyError:
            raise base.NotRegistered('%s is not registered' % cls)
        return cls._unregister(step_class)

    def validate(self, context):
        """Hook for custom context data validation. Should return a boolean
        value or raise :class:`~horizon.exceptions.WorkflowValidationError`.
        """
        return True

    def is_valid(self):
        """Verified that all required data is present in the context and
        calls the ``validate`` method to allow for finer-grained checks
        on the context data.
        """
        missing = self.depends_on - set(self.context.keys())
        if missing:
            raise exceptions.WorkflowValidationError(
                "Unable to complete the workflow. The values %s are "
                "required but not present." % ", ".join(missing))

        # Validate each step. Cycle through all of them to catch all errors
        # in one pass before returning.
        steps_valid = True
        for step in self.steps:
            if not step.action.is_valid():
                steps_valid = False
                step.has_errors = True
        if not steps_valid:
            return steps_valid
        return self.validate(self.context)

    def finalize(self):
        """Finalizes a workflow by running through all the actions in order
        and calling their ``handle`` methods. Returns ``True`` on full success,
        or ``False`` for a partial success, e.g. there were non-critical
        errors. (If it failed completely the function wouldn't return.)
        """
        partial = False
        for step in self.steps:
            try:
                data = step.action.handle(self.request, self.context)
                if data is True or data is None:
                    continue
                elif data is False:
                    partial = True
                else:
                    self.context = step.contribute(data or {}, self.context)
            except Exception:
                partial = True
                exceptions.handle(self.request)
        if not self.handle(self.request, self.context):
            partial = True
        return not partial

    def handle(self, request, context):
        """Handles any final processing for this workflow. Should return a
        boolean value indicating success.
        """
        return True

    def get_success_url(self):
        """Returns a URL to redirect the user to upon completion. By default it
        will attempt to parse a ``success_url`` attribute on the workflow,
        which can take the form of a reversible URL pattern name, or a
        standard HTTP URL.
        """
        try:
            return urlresolvers.reverse(self.success_url)
        except urlresolvers.NoReverseMatch:
            return self.success_url

    def format_status_message(self, message):
        """Hook to allow customization of the message returned to the user
        upon successful or unsuccessful completion of the workflow.

        By default it simply inserts the workflow's name into the message
        string.
        """
        if "%s" in message:
            return message % self.name
        else:
            return message

    def render(self):
        """Renders the workflow."""
        workflow_template = template.loader.get_template(self.template_name)
        extra_context = {"workflow": self}
        if self.request.is_ajax():
            extra_context['modal'] = True
        context = template.RequestContext(self.request, extra_context)
        return workflow_template.render(context)

    def get_absolute_url(self):
        """Returns the canonical URL for this workflow.

        This is used for the POST action attribute on the form element
        wrapping the workflow.

        For convenience it defaults to the value of
        ``request.get_full_path()`` with any query string stripped off,
        e.g. the path at which the workflow was requested.
        """
        return self.request.get_full_path().partition('?')[0]

    def add_error_to_step(self, message, slug):
        """Adds an error to the workflow's Step with the
        specified slug based on API issues. This is useful
        when you wish for API errors to appear as errors on
        the form rather than using the messages framework.
        """
        step = self.get_step(slug)
        if step:
            step.add_step_error(message)
