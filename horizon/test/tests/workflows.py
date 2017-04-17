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

from django import forms
from django import http
import mock

import six

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


class TestActionOne(workflows.Action):
    project_id = forms.ChoiceField(label="Project")
    user_id = forms.ChoiceField(label="User")

    class Meta(object):
        name = "Test Action One"
        slug = "test_action_one"

    def populate_project_id_choices(self, request, context):
        return [(PROJECT_ID, "test_project")]

    def populate_user_id_choices(self, request, context):
        return [(request.user.id, request.user.username)]

    def handle(self, request, context):
        return {"foo": "bar"}


class TestActionTwo(workflows.Action):
    instance_id = forms.CharField(label="Instance")

    class Meta(object):
        name = "Test Action Two"
        slug = "test_action_two"


class TestActionThree(workflows.Action):
    extra = forms.CharField(widget=forms.widgets.Textarea)

    class Meta(object):
        name = "Test Action Three"
        slug = "test_action_three"


class AdminAction(workflows.Action):
    admin_id = forms.CharField(label="Admin")

    class Meta(object):
        name = "Admin Action"
        slug = "admin_action"
        permissions = ("horizon.test",)


class TestDisabledAction(workflows.Action):
    disabled_id = forms.CharField(label="Disabled")

    class Meta(object):
        name = "Test Action Disabled"
        slug = "test_action_disabled"


class AdminForbiddenAction(workflows.Action):
    admin_id = forms.CharField(label="Admin forbidden")

    class Meta(object):
        name = "Admin Action"
        slug = "admin_action"
        policy_rules = (('action', 'forbidden'),)


class TestStepOne(workflows.Step):
    action_class = TestActionOne
    contributes = ("project_id", "user_id")


class TestStepTwo(workflows.Step):
    action_class = TestActionTwo
    depends_on = ("project_id",)
    contributes = ("instance_id",)
    connections = {"project_id":
                   (local_callback_func,
                    "horizon.test.tests.workflows.other_callback_func")}


class TestExtraStep(workflows.Step):
    action_class = TestActionThree
    depends_on = ("project_id",)
    contributes = ("extra_data",)
    connections = {"project_id": (extra_callback_func,)}
    after = TestStepOne
    before = TestStepTwo


class AdminStep(workflows.Step):
    action_class = AdminAction
    contributes = ("admin_id",)
    after = TestStepOne
    before = TestStepTwo


class TestDisabledStep(workflows.Step):
    action_class = TestDisabledAction
    contributes = ("disabled_id",)

    def allowed(self, request):
        return False


class AdminForbiddenStep(workflows.Step):
    action_class = AdminForbiddenAction


class TestWorkflow(workflows.Workflow):
    slug = "test_workflow"
    default_steps = (TestStepOne, TestStepTwo)


class TestWorkflowView(workflows.WorkflowView):
    workflow_class = TestWorkflow
    template_name = "workflow.html"


class TestFullscreenWorkflow(workflows.Workflow):
    slug = 'test_fullscreen_workflow'
    default_steps = (TestStepOne, TestStepTwo)
    fullscreen = True


class TestFullscreenWorkflowView(workflows.WorkflowView):
    workflow_class = TestFullscreenWorkflow
    template_name = "workflow.html"


class WorkflowsTests(test.TestCase):
    def setUp(self):
        super(WorkflowsTests, self).setUp()
        self.policy_patcher = mock.patch(
            'openstack_auth.policy.check', lambda action, request: True)
        self.policy_check = self.policy_patcher.start()
        self.addCleanup(mock.patch.stopall)

    def tearDown(self):
        super(WorkflowsTests, self).tearDown()
        self._reset_workflow()

    def _reset_workflow(self):
        TestWorkflow._cls_registry = set([])

    def test_workflow_construction(self):
        TestWorkflow.register(TestExtraStep)
        flow = TestWorkflow(self.request)
        self.assertQuerysetEqual(flow.steps,
                                 ['<TestStepOne: test_action_one>',
                                  '<TestExtraStep: test_action_three>',
                                  '<TestStepTwo: test_action_two>'])
        self.assertEqual(set(['project_id']), flow.depends_on)

    def test_step_construction(self):
        step_one = TestStepOne(TestWorkflow(self.request))
        # Action slug is moved from Meta by metaclass, and
        # Step inherits slug from action.
        self.assertEqual(TestActionOne.name, step_one.name)
        self.assertEqual(TestActionOne.slug, step_one.slug)
        # Handlers should be empty since there are no connections.
        self.assertEqual(step_one._handlers, {})

        step_two = TestStepTwo(TestWorkflow(self.request))
        # Handlers should be populated since we do have connections.
        self.assertEqual([local_callback_func, other_callback_func],
                         step_two._handlers["project_id"])

    def test_step_invalid_connections_handlers_not_list_or_tuple(self):
        class InvalidStepA(TestStepTwo):
            connections = {'project_id': {}}

        class InvalidStepB(TestStepTwo):
            connections = {'project_id': ''}

        with self.assertRaises(TypeError):
            InvalidStepA(TestWorkflow(self.request))

        with self.assertRaises(TypeError):
            InvalidStepB(TestWorkflow(self.request))

    def test_step_invalid_connection_handler_not_string_or_callable(self):
        class InvalidStepA(TestStepTwo):
            connections = {'project_id': (None,)}

        class InvalidStepB(TestStepTwo):
            connections = {'project_id': (0,)}

        with self.assertRaises(TypeError):
            InvalidStepA(TestWorkflow(self.request))

        with self.assertRaises(TypeError):
            InvalidStepB(TestWorkflow(self.request))

    def test_step_invalid_callback(self):
        # This should raise an exception
        class InvalidStep(TestStepTwo):
            connections = {"project_id": ('local_callback_func',)}

        with self.assertRaises(ValueError):
            InvalidStep(TestWorkflow(self.request))

    def test_connection_handlers_called(self):
        TestWorkflow.register(TestExtraStep)
        flow = TestWorkflow(self.request)

        # This should set the value without any errors, but trigger nothing
        flow.context['does_not_exist'] = False
        self.assertFalse(flow.context['does_not_exist'])

        # The order here is relevant. Note that we inserted "extra" between
        # steps one and two, and one has no handlers, so we should see
        # a response from extra, then one from each of step two's handlers.
        val = flow.context.set('project_id', PROJECT_ID)
        self.assertEqual([('test_action_three', 'extra'),
                          ('test_action_two', 'one'),
                          ('test_action_two', 'two')], val)

    def test_workflow_validation(self):
        flow = TestWorkflow(self.request)

        # Missing items fail validation.
        with self.assertRaises(exceptions.WorkflowValidationError):
            flow.is_valid()

        # All required items pass validation.
        seed = {"project_id": PROJECT_ID,
                "user_id": self.user.id,
                "instance_id": INSTANCE_ID}
        req = self.factory.post("/", seed)
        req.user = self.user
        flow = TestWorkflow(req, context_seed={"project_id": PROJECT_ID})
        for step in flow.steps:
            if not step.action.is_valid():
                self.fail("Step %s was unexpectedly invalid: %s"
                          % (step.slug, step.action.errors))
        self.assertTrue(flow.is_valid())

        # Additional items shouldn't affect validation
        flow.context.set("extra_data", "foo")
        self.assertTrue(flow.is_valid())

    def test_workflow_finalization(self):
        flow = TestWorkflow(self.request)
        self.assertTrue(flow.finalize())

    def test_workflow_view(self):
        view = TestWorkflowView.as_view()
        req = self.factory.get("/")
        res = view(req)
        self.assertEqual(200, res.status_code)

    def test_workflow_registration(self):
        req = self.factory.get("/foo")
        flow = TestWorkflow(req)
        self.assertQuerysetEqual(flow.steps,
                                 ['<TestStepOne: test_action_one>',
                                  '<TestStepTwo: test_action_two>'])

        TestWorkflow.register(TestExtraStep)
        flow = TestWorkflow(req)
        self.assertQuerysetEqual(flow.steps,
                                 ['<TestStepOne: test_action_one>',
                                  '<TestExtraStep: test_action_three>',
                                  '<TestStepTwo: test_action_two>'])

    def test_workflow_render(self):
        TestWorkflow.register(TestExtraStep)
        req = self.factory.get("/foo")
        flow = TestWorkflow(req)
        output = http.HttpResponse(flow.render())
        self.assertContains(output, six.text_type(flow.name))
        self.assertContains(output, six.text_type(TestActionOne.name))
        self.assertContains(output, six.text_type(TestActionTwo.name))
        self.assertContains(output, six.text_type(TestActionThree.name))

    def test_has_permissions(self):
        self.assertQuerysetEqual(TestWorkflow._cls_registry, [])
        TestWorkflow.register(AdminStep)
        flow = TestWorkflow(self.request)
        step = AdminStep(flow)

        self.assertItemsEqual(step.permissions,
                              ("horizon.test",))
        self.assertQuerysetEqual(flow.steps,
                                 ['<TestStepOne: test_action_one>',
                                  '<TestStepTwo: test_action_two>'])

        self.set_permissions(['test'])
        self.request.user = self.user
        flow = TestWorkflow(self.request)
        self.assertQuerysetEqual(flow.steps,
                                 ['<TestStepOne: test_action_one>',
                                  '<AdminStep: admin_action>',
                                  '<TestStepTwo: test_action_two>'])

    def test_has_allowed(self):
        TestWorkflow.register(TestDisabledStep)
        flow = TestWorkflow(self.request)
        # Check TestDisabledStep is not included
        # even though TestDisabledStep is registered.
        self.assertQuerysetEqual(flow.steps,
                                 ['<TestStepOne: test_action_one>',
                                  '<TestStepTwo: test_action_two>'])

    def test_step_is_hidden_on_policy(self):
        self.policy_patcher.stop()

        def policy_check(action, request):
            if action == (('action', 'forbidden'),):
                return False
            return True

        with mock.patch('openstack_auth.policy.check', policy_check):
            TestWorkflow.register(AdminForbiddenStep)
            flow = TestWorkflow(self.request)
            output = http.HttpResponse(flow.render())
            self.assertNotContains(output,
                                   six.text_type(AdminForbiddenAction.name))

    def test_entry_point(self):
        req = self.factory.get("/foo")
        flow = TestWorkflow(req)
        self.assertEqual("test_action_one", flow.get_entry_point())

        flow = TestWorkflow(req, entry_point="test_action_two")
        self.assertEqual("test_action_two", flow.get_entry_point())
