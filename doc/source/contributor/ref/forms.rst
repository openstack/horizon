=============
Horizon Forms
=============

Horizon ships with some very useful base form classes, form fields,
class-based views, and javascript helpers which streamline most of the common
tasks related to form handling.

Form Classes
============

.. automodule:: horizon.forms.base
    :members:

Form Fields
===========

.. automodule:: horizon.forms.fields
    :members:

Form Views
==========

.. automodule:: horizon.forms.views
    :members:

Forms Javascript
================

Switchable Fields
-----------------

By marking fields with the ``"switchable"`` and ``"switched"`` classes along
with defining a few data attributes you can programmatically hide, show,
and rename fields in a form.

The triggers are fields using a ``select`` input widget, marked with the
"switchable" class, and defining a "data-slug" attribute. When they are changed,
any input with the ``"switched"`` class and defining a ``"data-switch-on"``
attribute which matches the ``select`` input's ``"data-slug"`` attribute will be
evaluated for necessary changes. In simpler terms, if the ``"switched"`` target
input's ``"switch-on"`` matches the ``"slug"`` of the ``"switchable"`` trigger
input, it gets switched. Simple, right?

The ``"switched"`` inputs also need to define states. For each state in which
the input should be shown, it should define a data attribute like the
following: ``data-<slug>-<value>="<desired label>"``. When the switch event
happens the value of the ``"switchable"`` field will be compared to the
data attributes and the correct label will be applied to the field. If
a corresponding label for that value is *not* found, the field will
be hidden instead.

A simplified example is as follows::

    source = forms.ChoiceField(
        label=_('Source'),
        choices=[
            ('cidr', _('CIDR')),
            ('sg', _('Security Group'))
        ],
        widget=forms.ThemableSelectWidget(attrs={
            'class': 'switchable',
            'data-slug': 'source'
        })
    )

    cidr = fields.IPField(
        label=_("CIDR"),
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'switched',
            'data-switch-on': 'source',
            'data-source-cidr': _('CIDR')
        })
    )

    security_group = forms.ChoiceField(
        label=_('Security Group'),
        required=False,
        widget=forms.ThemableSelectWidget(attrs={
            'class': 'switched',
            'data-switch-on': 'source',
            'data-source-sg': _('Security Group')
        })
    )

That code would create the ``"switchable"`` control field ``source``, and the
two ``"switched"`` fields ``cidr`` and ``security group`` which are hidden or
shown depending on the value of ``source``.

.. note::

   A field can only safely define one slug in its ``"switch-on"`` attribute.
   While switching on multiple fields is possible, the behavior is very hard to
   predict due to the events being fired from the various switchable fields in
   order. You generally end up just having it hidden most of the time by
   accident, so it's not recommended. Instead just add a second field to the
   form and control the two independently, then merge their results in the
   form's clean or handle methods at the end.
