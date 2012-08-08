from django.utils.encoding import force_unicode
from django.utils.functional import lazy


def _lazy_join(separator, strings):
    return separator.join([force_unicode(s)
                           for s in strings])

lazy_join = lazy(_lazy_join, unicode)
