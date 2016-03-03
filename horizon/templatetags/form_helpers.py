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

import django.forms
from django import template as django_template


register = django_template.Library()


@register.filter
def add_bootstrap_class(field):
    """Add a "form-control" CSS class to the field's widget.

    This is so that Bootstrap styles it properly.
    """
    if not isinstance(field.field.widget, (
        django.forms.widgets.CheckboxInput,
        django.forms.widgets.CheckboxSelectMultiple,
        django.forms.widgets.RadioSelect,
        django.forms.widgets.FileInput,
        str,
    )):
        field_classes = set(field.field.widget.attrs.get('class', '').split())
        field_classes.add('form-control')
        field.field.widget.attrs['class'] = ' '.join(field_classes)
    return field


@register.filter
def is_checkbox(field):
    return isinstance(field.field.widget, django.forms.CheckboxInput)


@register.filter
def is_multiple_checkbox(field):
    return isinstance(field.field.widget, django.forms.CheckboxSelectMultiple)


@register.filter
def is_radio(field):
    return isinstance(field.field.widget, django.forms.RadioSelect)


@register.filter
def is_file(field):
    return isinstance(field.field.widget, django.forms.FileInput)


@register.filter
def add_item_url(field):
    if hasattr(field.field.widget, 'get_add_item_url'):
        return field.field.widget.get_add_item_url()
    return None


@register.filter
def wrapper_classes(field):
    classes = []
    if is_multiple_checkbox(field):
        classes.append('multiple-checkbox')
    return ' '.join(classes)
