# Copyright 2015 Cisco Systems, Inc.
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


from horizon.test import helpers as test
from horizon import views

from django import forms
from django.test import client
from django.utils.translation import ugettext_lazy as _
from django.views import generic

FAKENAME = "FakeName"


class ViewData(object):

    template_name = 'fake'

    def get_context_data(self, **kwargs):
        context = super(ViewData, self).get_context_data(**kwargs)
        context['object'] = {'name': 'myName'}
        return context


class PageWithNoTitle(ViewData, views.HorizonTemplateView):
    pass


class PageWithTitle(ViewData, views.HorizonTemplateView):
    page_title = "A Title"


class PageWithTitleData(ViewData, views.HorizonTemplateView):
    page_title = "A Title: {{ object.name }}"


class FormWithTitle(ViewData, views.HorizonFormView):
    form_class = forms.Form
    page_title = "A Title: {{ object.name }}"


class ViewWithTitle(views.PageTitleMixin, generic.TemplateView):
    page_title = "Fake"


class ViewWithTransTitle(views.PageTitleMixin, generic.TemplateView):
    page_title = _("Fake")


class PageTitleTests(test.TestCase):

    def setUp(self):
        super(PageTitleTests, self).setUp()
        self.request = client.RequestFactory().get('fake')

    def _dispatch(self, viewClass):
        p = viewClass()
        p.request = self.request
        return p.dispatch(self.request)

    def test_render_context_with_title(self):
        tm = ViewWithTitle()
        context = tm.render_context_with_title({})
        self.assertEqual("Fake", context['page_title'])

    def test_render_context_with_title_override(self):
        tm = ViewWithTitle()
        context = tm.render_context_with_title({'page_title': "ekaF"})
        self.assertEqual("ekaF", context['page_title'])

    def test_render_context_with_title_lazy_translations(self):
        tm = ViewWithTransTitle()
        context = tm.render_context_with_title({})
        self.assertEqual("Fake", context['page_title'])

    def test_no_title_set(self):
        res = self._dispatch(PageWithNoTitle)
        self.assertEqual("", res.context_data['page_title'])

    def test_title_set(self):
        res = self._dispatch(PageWithTitle)
        self.assertEqual("A Title", res.context_data['page_title'])

    def test_title_with_data(self):
        res = self._dispatch(PageWithTitleData)
        self.assertEqual("A Title: myName", res.context_data['page_title'])

    def test_form_with_title(self):
        res = self._dispatch(FormWithTitle)
        self.assertEqual("A Title: myName", res.context_data['page_title'])
