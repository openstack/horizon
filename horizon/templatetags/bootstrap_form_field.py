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
from django import template as django_template

register = django_template.Library()


@register.filter
def bootstrap_form_field(element):
    markup_classes = {'label': '', 'value': '', 'single_value': ''}
    return render(element, markup_classes)


def add_input_classes(field):
    if (not is_checkbox(field) and
            not is_multiple_checkbox(field) and
            not is_radio(field) and
            not is_file(field)):
        field_classes = field.field.widget.attrs.get('class', '')
        field_classes += ' form-control'
        field.field.widget.attrs['class'] = field_classes


def render(element, markup_classes):
    add_input_classes(element)
    template = django_template.loader.get_template(
        "horizon/common/_bootstrap_form_field.html")
    context = django_template.Context({'field': element,
                                       'classes': markup_classes})

    return template.render(context)


@register.filter
def is_checkbox(field):
    return isinstance(field.field.widget, forms.CheckboxInput)


@register.filter
def is_multiple_checkbox(field):
    return isinstance(field.field.widget, forms.CheckboxSelectMultiple)


@register.filter
def is_radio(field):
    return isinstance(field.field.widget, forms.RadioSelect)


@register.filter
def is_file(field):
    return isinstance(field.field.widget, forms.FileInput)


@register.filter
def is_dynamic_select(field):
    return hasattr(field.field.widget, 'add_item_link')


@register.filter
def wrapper_classes(field):
    classes = []
    if is_multiple_checkbox(field):
        classes.append('multiple-checkbox')
    if is_dynamic_select(field):
        classes.append('dynamic-select')
    return ' '.join(classes)
