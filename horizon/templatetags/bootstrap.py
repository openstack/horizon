# Copyright 2015 Hewlett Packard Enterprise Software, LLC
# All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

from __future__ import absolute_import

from django import template


register = template.Library()


@register.inclusion_tag('bootstrap/progress_bar.html')
def bs_progress_bar(*args, **kwargs):
    """A Standard Bootstrap Progress Bar.
    http://getbootstrap.com/components/#progress

    param args (Array of Numbers: 0-100): Percent of Progress Bars
    param context (String): Adds 'progress-bar-{context} to the class attribute
    param contexts (Array of Strings): Cycles through contexts for stacked bars
    param text (Boolean): True: shows value within the bar, False: uses sr span
    param striped (Boolean): Adds 'progress-bar-striped' to the class attribute
    param animated (Boolean): Adds 'active' to the class attribute if striped
    param min_val (0): Used for the aria-min value
    param max_val (0): Used for the aria-max value
    """

    bars = []
    contexts = kwargs.get(
        'contexts',
        ['', 'success', 'info', 'warning', 'danger']
    )

    for ndx, arg in enumerate(args):
        bars.append(
            dict(percent=arg,
                 context=kwargs.get('context', contexts[ndx % len(contexts)]))
        )

    return {
        'bars': bars,
        'text': kwargs.pop('text', False),
        'striped': kwargs.pop('striped', False),
        'animated': kwargs.pop('animated', False),
        'min_val': kwargs.pop('min_val', 0),
        'max_val': kwargs.pop('max_val', 100),
    }
