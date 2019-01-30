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

from django import shortcuts

from horizon import forms
from horizon.test import helpers as test


class FormMixinTests(test.TestCase):

    def _prepare_view(self, cls, request_headers, *args, **kwargs):
        req = self.factory.get('/my_url/', **request_headers)
        req.user = self.user
        view = cls()
        view.request = req
        view.args = args
        view.kwargs = kwargs
        view.template_name = 'test_template'
        # Note(Itxaka): ModalFormView requires a form_class to behave properly
        view.form_class = TestForm
        return view

    def test_modal_form_mixin_hide_true_if_ajax(self):
        view = self._prepare_view(
            forms.views.ModalFormView,
            dict(HTTP_X_REQUESTED_WITH='XMLHttpRequest'))
        context = view.get_context_data()
        self.assertTrue(context['hide'])

    def test_modal_form_mixin_add_to_field_header_set(self):
        return self._test_form_mixin_add_to_field_header(add_field=True)

    def test_modal_form_mixin_add_to_field_header_not_set(self):
        return self._test_form_mixin_add_to_field_header(add_field=False)

    def _test_form_mixin_add_to_field_header(self, add_field=False):
        options = dict(HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        if add_field:
            options[forms.views.ADD_TO_FIELD_HEADER] = "keepme"

        view = self._prepare_view(forms.views.ModalFormView, options)
        context = view.get_context_data()

        if add_field:
            self.assertEqual("keepme", context['add_to_field'])
        else:
            self.assertNotIn('add_to_field', context)

    def test_template_name_change_based_on_ajax_request(self):
        view = self._prepare_view(
            forms.views.ModalFormView,
            dict(HTTP_X_REQUESTED_WITH='XMLHttpRequest'))
        self.assertEqual('_' + view.template_name,
                         view.get_template_names())

        view = self._prepare_view(forms.views.ModalFormView, {})
        self.assertEqual(view.template_name, view.get_template_names())


class TestForm(forms.SelfHandlingForm):

    name = forms.CharField(max_length=255)

    def handle(self, request, data):
        return True


class FormErrorTests(test.TestCase):

    template = 'horizon/common/_form_fields.html'

    def setUp(self):
        super(FormErrorTests, self).setUp()
        # Note(Itxaka): We pass data to the form so its bound and has the
        # proper cleaned_data fields
        self.form = TestForm(self.request, data={'fake': 'data'})

    def _render_form(self):
        return shortcuts.render(self.request, self.template,
                                {'form': self.form})

    def test_set_warning(self):
        warning_text = 'WARNING 29380'
        self.form.set_warning(warning_text)
        self.assertEqual([warning_text], self.form.warnings)
        resp = self._render_form()
        self.assertIn(warning_text.encode('utf-8'), resp.content)

    def test_api_error(self):
        error_text = 'ERROR 12938'
        self.form.full_clean()
        self.form.api_error(error_text)
        self.assertEqual([error_text], self.form.non_field_errors())
        resp = self._render_form()
        self.assertIn(error_text.encode('utf-8'), resp.content)
