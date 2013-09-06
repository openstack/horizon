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

from django import forms
from django import http

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

    class Meta:
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

    class Meta:
        name = "Test Action Two"
        slug = "test_action_two"


class TestActionThree(workflows.Action):
    extra = forms.CharField(widget=forms.widgets.Textarea)

    class Meta:
        name = "Test Action Three"
        slug = "test_action_three"


class AdminAction(workflows.Action):
    admin_id = forms.CharField(label="Admin")

    class Meta:
        name = "Admin Action"
        slug = "admin_action"
        permissions = ("horizon.test",)


class TestStepOne(workflows.Step):
    action_class = TestActionOne
    contributes = ("project_id", "user_id")


class TestStepTwo(workflows.Step):
    action_class = TestActionTwo
    depends_on = ("project_id",)
    contributes = ("instance_id",)
    connections = {"project_id": (local_callback_func,
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


class TestWorkflow(workflows.Workflow):
    slug = "test_workflow"
    default_steps = (TestStepOne, TestStepTwo)


class TestWorkflowView(workflows.WorkflowView):
    workflow_class = TestWorkflow
    template_name = "workflow.html"


class WorkflowsTests(test.TestCase):
    def setUp(self):
        super(WorkflowsTests, self).setUp()

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
        self.assertEqual(flow.depends_on, set(['project_id']))

    def test_step_construction(self):
        step_one = TestStepOne(TestWorkflow(self.request))
        # Action slug is moved from Meta by metaclass, and
        # Step inherits slug from action.
        self.assertEqual(step_one.name, TestActionOne.name)
        self.assertEqual(step_one.slug, TestActionOne.slug)
        # Handlers should be empty since there are no connections.
        self.assertEqual(step_one._handlers, {})

        step_two = TestStepTwo(TestWorkflow(self.request))
        # Handlers should be populated since we do have connections.
        self.assertEqual(step_two._handlers["project_id"],
                         [local_callback_func, other_callback_func])

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
        self.assertEqual(flow.context['does_not_exist'], False)

        # The order here is relevant. Note that we inserted "extra" between
        # steps one and two, and one has no handlers, so we should see
        # a response from extra, then one from each of step two's handlers.
        val = flow.context.set('project_id', PROJECT_ID)
        self.assertEqual(val, [('test_action_three', 'extra'),
                               ('test_action_two', 'one'),
                               ('test_action_two', 'two')])

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
        self.assertEqual(res.status_code, 200)

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
        self.assertContains(output, unicode(flow.name))
        self.assertContains(output, unicode(TestActionOne.name))
        self.assertContains(output, unicode(TestActionTwo.name))
        self.assertContains(output, unicode(TestActionThree.name))

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

    def test_entry_point(self):
        req = self.factory.get("/foo")
        flow = TestWorkflow(req)
        self.assertEqual(flow.get_entry_point(), "test_action_one")

        flow = TestWorkflow(req, entry_point="test_action_two")
        self.assertEqual(flow.get_entry_point(), "test_action_two")
