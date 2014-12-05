# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.
import decimal

import pint

from horizon.utils import functions

# Mapping of units from Ceilometer to Pint
INFORMATION_UNITS = (
    ('B', 'byte'),
    ('KB', 'Kibyte'),
    ('MB', 'Mibyte'),
    ('GB', 'Gibyte'),
    ('TB', 'Tibyte'),
    ('PB', 'Pibyte'),
    ('EB', 'Eibyte'),
)

TIME_UNITS = ('ns', 's', 'min', 'hr', 'day', 'week', 'month', 'year')


ureg = pint.UnitRegistry()


def is_supported(unit):
    """Returns a bool indicating whether the unit specified is supported by
    this module.
    """
    return unit in functions.get_keys(INFORMATION_UNITS) + TIME_UNITS


def is_larger(unit_1, unit_2):
    """Returns a boolean indicating whether unit_1 is larger than unit_2.

    E.g:

    >>> is_larger('KB', 'B')
    True
    >>> is_larger('min', 'day')
    False
    """
    unit_1 = functions.value_for_key(INFORMATION_UNITS, unit_1)
    unit_2 = functions.value_for_key(INFORMATION_UNITS, unit_2)

    return ureg.parse_expression(unit_1) > ureg.parse_expression(unit_2)


def convert(value, source_unit, target_unit, fmt=False):
    """Converts value from source_unit to target_unit. Returns a tuple
    containing the converted value and target_unit.  Having fmt set to True
    causes the value to be formatted to 1 decimal digit if it's a decimal or
    be formatted as integer if it's an integer.

    E.g:

    >>> convert(2, 'hr', 'min')
    (120.0, 'min')
    >>> convert(2, 'hr', 'min', fmt=True)
    (120, 'min')
    >>> convert(30, 'min', 'hr', fmt=True)
    (0.5, 'hr')
    """
    orig_target_unit = target_unit
    source_unit = functions.value_for_key(INFORMATION_UNITS, source_unit)
    target_unit = functions.value_for_key(INFORMATION_UNITS, target_unit)

    q = ureg.Quantity(value, source_unit)
    q = q.to(ureg.parse_expression(target_unit))
    value = functions.format_value(q.magnitude) if fmt else q.magnitude
    return value, orig_target_unit


def normalize(value, unit):
    """Converts the value so that it belongs to some expected range.
    Returns the new value and new unit.

    E.g:

    >>> normalize(1024, 'KB')
    (1, 'MB')
    >>> normalize(90, 'min')
    (1.5, 'hr')
    >>> normalize(1.0, 'object')
    (1, 'object')
    """
    if value < 0:
        raise ValueError('Negative value: %s %s.' % (value, unit))

    if unit in functions.get_keys(INFORMATION_UNITS):
        return _normalize_information(value, unit)
    elif unit in TIME_UNITS:
        return _normalize_time(value, unit)
    else:
        # Unknown unit, just return it
        return functions.format_value(value), unit


def _normalize_information(value, unit):
    value = decimal.Decimal(str(value))

    while value < 1:
        prev_unit = functions.previous_key(INFORMATION_UNITS, unit)
        if prev_unit is None:
            break
        value, unit = convert(value, unit, prev_unit)

    while value >= 1024:
        next_unit = functions.next_key(INFORMATION_UNITS, unit)
        if next_unit is None:
            break
        value, unit = convert(value, unit, next_unit)

    return functions.format_value(value), unit


def _normalize_time(value, unit):
    # Normalize time by converting to next higher unit when value is
    # at least 2 units
    value, unit = convert(value, unit, 's')

    if value >= 120:
        value, unit = convert(value, 's', 'min')

        if value >= 120:
            value, unit = convert(value, 'min', 'hr')

            if value >= 48:
                value, unit = convert(value, 'hr', 'day')

                if value >= 730:
                    value, unit = convert(value, 'day', 'year')
                elif value >= 62:
                    value, unit = convert(value, 'day', 'month')
                elif value >= 14:
                    value, unit = convert(value, 'day', 'week')

    return functions.format_value(value), unit
