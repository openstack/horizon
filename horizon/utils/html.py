import copy

from django.forms.util import flatatt  # noqa


class HTMLElement(object):
    """ A generic base class that gracefully handles html-style attributes. """
    def __init__(self):
        self.attrs = getattr(self, "attrs", {})
        self.classes = getattr(self, "classes", [])

    def get_default_classes(self):
        """
        Returns an iterable of default classes which should be combined with
        any other declared classes.
        """
        return []

    def get_default_attrs(self):
        """
        Returns a dict of default attributes which should be combined with
        other declared attributes.
        """
        return {}

    def get_final_attrs(self):
        """
        Returns a dict containing the final attributes of this element
        which will be rendered.
        """
        final_attrs = copy.copy(self.get_default_attrs())
        final_attrs.update(self.attrs)
        # Handle css class concatenation
        default = " ".join(self.get_default_classes())
        defined = self.attrs.get('class', '')
        additional = " ".join(getattr(self, "classes", []))
        non_empty = [test for test in (defined, default, additional) if test]
        final_classes = " ".join(non_empty).strip()
        final_attrs.update({'class': final_classes})
        return final_attrs

    @property
    def attr_string(self):
        """
        Returns a flattened string of HTML attributes based on the
        ``attrs`` dict provided to the class.
        """
        return flatatt(self.get_final_attrs())

    @property
    def class_string(self):
        """
        Returns a list of class name of HTML Element in string
        """
        classes_str = " ".join(self.classes)
        return classes_str
