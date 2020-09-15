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

from unittest import mock

from django import forms
from django import http
from django.test.utils import override_settings

from horizon import base
from horizon import exceptions
from horizon.test import helpers as test
from horizon import workflows


PROJECT_ID = "a23lkjre389fwenj"
INSTANCE_ID = "sdlkjhf9832roiw"


def local_callback_func(request, context):
    return "one"


def other_callback_func(request, context):
    return "two"


def extra_callback_func(request, context):
    return "extra"


class ActionOne(workflows.Action):
    project_id = forms.ChoiceField(label="Project")
    user_id = forms.ChoiceField(label="User")

    class Meta(object):
        name = "Action One"
        slug = "action_one"

    def populate_project_id_choices(self, request, context):
        return [(PROJECT_ID, "test_project")]

    def populate_user_id_choices(self, request, context):
        return [(request.user.id, request.user.username)]

    def handle(self, request, context):
        return {"foo": "bar"}


class ActionTwo(workflows.Action):
    instance_id = forms.CharField(label="Instance")

    class Meta(object):
        name = "Action Two"
        slug = "action_two"


class ActionThree(workflows.Action):
    extra = forms.CharField(widget=forms.widgets.Textarea)

    class Meta(object):
        name = "Action Three"
        slug = "action_three"


class ActionFour(workflows.Action):
    field_four = forms.CharField(widget=forms.widgets.Textarea)

    class Meta(object):
        name = "Action Four"
        slug = "action_four"


class AdminAction(workflows.Action):
    admin_id = forms.CharField(label="Admin")

    class Meta(object):
        name = "Admin Action"
        slug = "admin_action"
        permissions = ("horizon.test",)


class DisabledAction(workflows.Action):
    disabled_id = forms.CharField(label="Disabled")

    class Meta(object):
        name = "Action Disabled"
        slug = "action_disabled"


class AdminForbiddenAction(workflows.Action):
    admin_id = forms.CharField(label="Admin forbidden")

    class Meta(object):
        name = "Admin Action"
        slug = "admin_action"
        policy_rules = (('action', 'forbidden'),)


class StepOne(workflows.Step):
    action_class = ActionOne
    contributes = ("project_id", "user_id")


class StepTwo(workflows.Step):
    action_class = ActionTwo
    depends_on = ("project_id",)
    contributes = ("instance_id",)
    connections = {"project_id":
                   (local_callback_func,
                    "horizon.test.unit.workflows.test_workflows."
                    "other_callback_func")}


class StepThree(workflows.Step):
    action_class = ActionThree
    depends_on = ("project_id",)
    contributes = ("extra_data",)
    connections = {"project_id": (extra_callback_func,)}
    after = StepOne
    before = StepTwo


class StepFour(workflows.Step):
    action_class = ActionFour
    contributes = ("field_four",)


class AdminStep(workflows.Step):
    action_class = AdminAction
    contributes = ("admin_id",)
    after = StepOne
    before = StepTwo


class DisabledStep(workflows.Step):
    action_class = DisabledAction
    contributes = ("disabled_id",)

    def allowed(self, request):
        return False


class AdminForbiddenStep(workflows.Step):
    action_class = AdminForbiddenAction


class WorkflowForTesting(workflows.Workflow):
    slug = "test_workflow"
    default_steps = (StepOne, StepTwo)


class WorkflowWithConfig(workflows.Workflow):
    slug = "test_workflow"
    default_steps = (StepOne,)


class WorkflowViewForTesting(workflows.WorkflowView):
    workflow_class = WorkflowForTesting
    template_name = "workflow.html"


class FullscreenWorkflow(workflows.Workflow):
    slug = 'test_fullscreen_workflow'
    default_steps = (StepOne, StepTwo)
    fullscreen = True


class FullscreenWorkflowView(workflows.WorkflowView):
    workflow_class = FullscreenWorkflow
    template_name = "workflow.html"


class WorkflowsTests(test.TestCase):
    def setUp(self):
        super().setUp()
        self.policy_patcher = mock.patch(
            'openstack_auth.policy.check', lambda action, request: True)
        self.policy_check = self.policy_patcher.start()
        self.addCleanup(mock.patch.stopall)

    def tearDown(self):
        super().tearDown()
        self._reset_workflow()

    def _reset_workflow(self):
        WorkflowForTesting._cls_registry = []

    def test_workflow_construction(self):
        WorkflowForTesting.register(StepThree)
        flow = WorkflowForTesting(self.request)
        self.assertQuerysetEqual(flow.steps,
                                 ['<StepOne: action_one>',
                                  '<StepThree: action_three>',
                                  '<StepTwo: action_two>'])
        self.assertEqual(set(['project_id']), flow.depends_on)

    @test.update_settings(HORIZON_CONFIG={'extra_steps': {
        'horizon.test.unit.workflows.test_workflows.WorkflowWithConfig': (
            'horizon.test.unit.workflows.test_workflows.StepTwo',
            'horizon.test.unit.workflows.test_workflows.StepThree',
            'horizon.test.unit.workflows.test_workflows.StepFour',
        ),
    }})
    def test_workflow_construction_with_config(self):
        flow = WorkflowWithConfig(self.request)
        # NOTE: StepThree must be placed between StepOne and
        # StepTwo in honor of before/after of StepThree.
        self.assertQuerysetEqual(flow.steps,
                                 ['<StepOne: action_one>',
                                  '<StepThree: action_three>',
                                  '<StepTwo: action_two>',
                                  '<StepFour: action_four>',
                                  ])

    def test_step_construction(self):
        step_one = StepOne(WorkflowForTesting(self.request))
        # Action slug is moved from Meta by metaclass, and
        # Step inherits slug from action.
        self.assertEqual(ActionOne.name, step_one.name)
        self.assertEqual(ActionOne.slug, step_one.slug)
        # Handlers should be empty since there are no connections.
        self.assertEqual(step_one._handlers, {})

        step_two = StepTwo(WorkflowForTesting(self.request))
        # Handlers should be populated since we do have connections.
        self.assertEqual([local_callback_func, other_callback_func],
                         step_two._handlers["project_id"])

    def test_step_invalid_connections_handlers_not_list_or_tuple(self):
        class InvalidStepA(StepTwo):
            connections = {'project_id': {}}

        class InvalidStepB(StepTwo):
            connections = {'project_id': ''}

        with self.assertRaises(TypeError):
            InvalidStepA(WorkflowForTesting(self.request))

        with self.assertRaises(TypeError):
            InvalidStepB(WorkflowForTesting(self.request))

    def test_step_invalid_connection_handler_not_string_or_callable(self):
        class InvalidStepA(StepTwo):
            connections = {'project_id': (None,)}

        class InvalidStepB(StepTwo):
            connections = {'project_id': (0,)}

        with self.assertRaises(TypeError):
            InvalidStepA(WorkflowForTesting(self.request))

        with self.assertRaises(TypeError):
            InvalidStepB(WorkflowForTesting(self.request))

    def test_step_invalid_callback(self):
        # This should raise an exception
        class InvalidStep(StepTwo):
            connections = {"project_id": ('local_callback_func',)}

        with self.assertRaises(ValueError):
            InvalidStep(WorkflowForTesting(self.request))

    def test_connection_handlers_called(self):
        WorkflowForTesting.register(StepThree)
        flow = WorkflowForTesting(self.request)

        # This should set the value without any errors, but trigger nothing
        flow.context['does_not_exist'] = False
        self.assertFalse(flow.context['does_not_exist'])

        # The order here is relevant. Note that we inserted "extra" between
        # steps one and two, and one has no handlers, so we should see
        # a response from extra, then one from each of step two's handlers.
        val = flow.context.set('project_id', PROJECT_ID)
        self.assertEqual([('action_three', 'extra'),
                          ('action_two', 'one'),
                          ('action_two', 'two')], val)

    def test_workflow_validation(self):
        flow = WorkflowForTesting(self.request)

        # Missing items fail validation.
        with self.assertRaises(exceptions.WorkflowValidationError):
            flow.is_valid()

        # All required items pass validation.
        seed = {"project_id": PROJECT_ID,
                "user_id": self.user.id,
                "instance_id": INSTANCE_ID}
        req = self.factory.post("/", seed)
        req.user = self.user
        flow = WorkflowForTesting(req, context_seed={"project_id": PROJECT_ID})
        for step in flow.steps:
            if not step.action.is_valid():
                self.fail("Step %s was unexpectedly invalid: %s"
                          % (step.slug, step.action.errors))
        self.assertTrue(flow.is_valid())

        # Additional items shouldn't affect validation
        flow.context.set("extra_data", "foo")
        self.assertTrue(flow.is_valid())

    def test_workflow_finalization(self):
        flow = WorkflowForTesting(self.request)
        self.assertTrue(flow.finalize())

    def test_workflow_view(self):
        view = WorkflowViewForTesting.as_view()
        req = self.factory.get("/")
        res = view(req)
        self.assertEqual(200, res.status_code)

    def test_workflow_registration(self):
        req = self.factory.get("/foo")
        flow = WorkflowForTesting(req)
        self.assertQuerysetEqual(flow.steps,
                                 ['<StepOne: action_one>',
                                  '<StepTwo: action_two>'])

        WorkflowForTesting.register(StepThree)
        flow = WorkflowForTesting(req)
        self.assertQuerysetEqual(flow.steps,
                                 ['<StepOne: action_one>',
                                  '<StepThree: action_three>',
                                  '<StepTwo: action_two>'])

    def test_workflow_unregister_unexisting_workflow(self):
        with self.assertRaises(base.NotRegistered):
            WorkflowForTesting.unregister(DisabledStep)

    def test_workflow_render(self):
        WorkflowForTesting.register(StepThree)
        req = self.factory.get("/foo")
        flow = WorkflowForTesting(req)
        output = http.HttpResponse(flow.render())
        self.assertContains(output, flow.name)
        self.assertContains(output, ActionOne.name)
        self.assertContains(output, ActionTwo.name)
        self.assertContains(output, ActionThree.name)

    def test_has_permissions(self):
        self.assertQuerysetEqual(WorkflowForTesting._cls_registry, [])
        WorkflowForTesting.register(AdminStep)
        flow = WorkflowForTesting(self.request)
        step = AdminStep(flow)

        self.assertCountEqual(step.permissions,
                              ("horizon.test",))
        self.assertQuerysetEqual(flow.steps,
                                 ['<StepOne: action_one>',
                                  '<StepTwo: action_two>'])

        self.set_permissions(['test'])
        self.request.user = self.user
        flow = WorkflowForTesting(self.request)
        self.assertQuerysetEqual(flow.steps,
                                 ['<StepOne: action_one>',
                                  '<AdminStep: admin_action>',
                                  '<StepTwo: action_two>'])

    def test_has_allowed(self):
        WorkflowForTesting.register(DisabledStep)
        flow = WorkflowForTesting(self.request)
        # Check DisabledStep is not included
        # even though DisabledStep is registered.
        self.assertQuerysetEqual(flow.steps,
                                 ['<StepOne: action_one>',
                                  '<StepTwo: action_two>'])

    def test_step_is_hidden_on_policy(self):
        self.policy_patcher.stop()

        def policy_check(action, request):
            if action == (('action', 'forbidden'),):
                return False
            return True

        with mock.patch('openstack_auth.policy.check', policy_check):
            WorkflowForTesting.register(AdminForbiddenStep)
            flow = WorkflowForTesting(self.request)
            output = http.HttpResponse(flow.render())
            self.assertNotContains(output, AdminForbiddenAction.name)

    def test_entry_point(self):
        req = self.factory.get("/foo")
        flow = WorkflowForTesting(req)
        self.assertEqual("action_one", flow.get_entry_point())

        flow = WorkflowForTesting(req, entry_point="action_two")
        self.assertEqual("action_two", flow.get_entry_point())

    @override_settings(ALLOWED_HOSTS=['localhost'])
    def test_redirect_url_safe(self):
        url = 'http://localhost/test'
        view = WorkflowViewForTesting()
        request = self.factory.get("/", data={
            'next': url,
        })
        request.META['SERVER_NAME'] = "localhost"
        view.request = request
        context = view.get_context_data()
        self.assertEqual(url, context['REDIRECT_URL'])

    @override_settings(ALLOWED_HOSTS=['localhost'])
    def test_redirect_url_unsafe(self):
        url = 'http://evilcorp/test'
        view = WorkflowViewForTesting()
        request = self.factory.get("/", data={
            'next': url,
        })
        request.META['SERVER_NAME'] = "localhost"
        view.request = request
        context = view.get_context_data()
        self.assertIsNone(context['REDIRECT_URL'])
