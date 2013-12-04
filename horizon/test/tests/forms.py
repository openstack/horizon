# vim: tabstop=4 shiftwidth=4 softtabstop=4

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
        return view

    def test_modal_form_mixin_hide_true_if_ajax(self):
        view = self._prepare_view(forms.views.ModalFormView,
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
            self.assertEqual(context['add_to_field'], "keepme")
        else:
            self.assertNotIn('add_to_field', context)

    def test_template_name_change_based_on_ajax_request(self):
            view = self._prepare_view(forms.views.ModalFormView,
                dict(HTTP_X_REQUESTED_WITH='XMLHttpRequest'))
            self.assertEqual(view.get_template_names(),
                             '_' + view.template_name)

            view = self._prepare_view(forms.views.ModalFormView, {})
            self.assertEqual(view.get_template_names(), view.template_name)
