.. _topics-workflows:

======================
Workflows Topic Guide
======================

One of the most challenging aspects of building a compelling user experience
is crafting complex multi-part workflows. Horizon's ``workflows`` module
aims to bring that capability within everyday reach.

.. seealso::

   For detailed API information refer to the :ref:`ref-workflows`.

Workflows
=========

Workflows are complex forms with tabs, each workflow must consist of classes
extending the :class:`~horizon.workflows.Workflow`,
:class:`~horizon.workflows.Step` and :class:`~horizon.workflows.Action`

Complex example of a workflow
------------------------------

The following is a complex example of how data is exchanged between
urls, views, workflows and templates:

#. In ``urls.py``, we have the named parameter. E.g. ``resource_class_id``. ::

    RESOURCE_CLASS = r'^(?P<resource_class_id>[^/]+)/%s$'

    urlpatterns = [
        url(RESOURCE_CLASS % 'update', UpdateView.as_view(), name='update')
    ]

#. In ``views.py``, we pass data to the template and to the action(form)
   (action can also pass data to the ``get_context_data`` method and to the
   template). ::

    class UpdateView(workflows.WorkflowView):
        workflow_class = UpdateResourceClass

        def get_context_data(self, **kwargs):
            context = super(UpdateView, self).get_context_data(**kwargs)
            # Data from URL are always in self.kwargs, here we pass the data
            # to the template.
            context["resource_class_id"] = self.kwargs['resource_class_id']
            # Data contributed by Workflow's Steps are in the
            # context['workflow'].context list. We can use that in the
            # template too.
            return context

        def _get_object(self, *args, **kwargs):
            # Data from URL are always in self.kwargs, we can use them here
            # to load our object of interest.
            resource_class_id = self.kwargs['resource_class_id']
            # Code omitted, this method should return some object obtained
            # from API.

        def get_initial(self):
            resource_class = self._get_object()
            # This data will be available in the Action's methods and
            # Workflow's handle method.
            # But only if the steps will depend on them.
            return {'resource_class_id': resource_class.id,
                    'name': resource_class.name,
                    'service_type': resource_class.service_type}

#. In ``workflows.py`` we process the data, it is just more complex django
   form. ::

    class ResourcesAction(workflows.Action):
        # The name field will be automatically available in all action's
        # methods.
        # If we want this field to be used in the another Step or Workflow,
        # it has to be contributed by this step, then depend on in another
        # step.
        name = forms.CharField(max_length=255,
                               label=_("Testing Name"),
                               help_text="")

        def handle(self, request, data):
            pass
            # If we want to use some data from the URL, the Action's step
            # has to depend on them. It's then available in
            # self.initial['resource_class_id'] or data['resource_class_id'].
            # In other words, resource_class_id has to be passed by view's
            # get_initial and listed in step's depends_on list.

            # We can also use here the data from the other steps. If we want
            # the data from the other step, the step needs to contribute the
            # data and the steps needs to be ordered properly.

    class UpdateResources(workflows.Step):
        action_class = ResourcesAction
        # This passes data from Workflow context to action methods
        # (handle, clean). Workflow context consists of URL data and data
        # contributed by other steps.
        depends_on = ("resource_class_id",)

        # By contributing, the data on these indexes will become available to
        # Workflow and to other Steps (if they will depend on them). Notice,
        # that the resources_object_ids key has to be manually added in
        # contribute method first.
        contributes = ("resources_object_ids", "name")

        def contribute(self, data, context):
            # We can obtain the http request from workflow.
            request = self.workflow.request
            if data:
                # Only fields defined in Action are automatically
                # available for contribution. If we want to contribute
                # something else, We need to override the contribute method
                # and manually add it to the dictionary.
                context["resources_object_ids"] =\
                    request.POST.getlist("resources_object_ids")

            # We have to merge new context with the passed data or let
            # the superclass do this.
            context.update(data)
            return context

    class UpdateResourceClass(workflows.Workflow):
        default_steps = (UpdateResources,)

        def handle(self, request, data):
            pass
            # This method is called as last (after all Action's handle
            # methods). All data that are listed in step's 'contributes='
            # and 'depends_on=' are available here.
            # It can be easier to have the saving logic only here if steps
            # are heavily connected or complex.

            # data["resources_object_ids"], data["name"] and
            # data["resources_class_id"] are available here.
