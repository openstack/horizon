from django import forms
from django.template import Context
from django.template.loader import get_template
from django import template

register = template.Library()

@register.filter
def bootstrap_form_field(element):
    markup_classes = {'label': '', 'value': '', 'single_value': ''}
    return render(element, markup_classes)


def add_input_classes(field):
    if not is_checkbox(field) and not is_multiple_checkbox(field) and not is_radio(field) \
        and not is_file(field):
        field_classes = field.field.widget.attrs.get('class', '')
        field_classes += ' form-control'
        field.field.widget.attrs['class'] = field_classes


def render(element, markup_classes):
    add_input_classes(element)
    template = get_template("horizon/common/_bootstrap_form_field.html")
    context = Context({'field': element, 'classes': markup_classes})

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
