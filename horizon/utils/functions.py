import math

from django.utils.encoding import force_unicode
from django.utils.functional import lazy


def _lazy_join(separator, strings):
    return separator.join([force_unicode(s)
                           for s in strings])

lazy_join = lazy(_lazy_join, unicode)


def bytes_to_gigabytes(bytes):
    # Converts the number of bytes to the next highest number of Gigabytes
    # For example 5000000 (5 Meg) would return '1'
    return int(math.ceil(float(bytes) / 1024 ** 3))
