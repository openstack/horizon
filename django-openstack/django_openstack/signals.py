# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright 2011 United States Government as represented by the
# Administrator of the National Aeronautics and Space Administration.
# All Rights Reserved.
#
# Copyright 2011 Nebula, Inc.
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

import django.dispatch
from django.dispatch import receiver

dash_modules_ping = django.dispatch.Signal()
dash_modules_urls = django.dispatch.Signal()


def dash_modules_detect():
    """
    Sends a pinging signal to the app, all listening modules will reply with
    items for the sidebar.

    The response is a tuple of the Signal object instance, and a dictionary.
    The values within the dictionary containing links and a title which should
    be added to the sidebar navigation.

    Example: (<dash_apps_ping>,
              {'title': 'Nixon',
               'links': [{'url':'/syspanel/nixon/google',
                          'text':'Google', 'active_text': 'google'}],
               'type': syspanel})
    """
    return dash_modules_ping.send(sender=dash_modules_ping)


def dash_app_setup_urls():
    """
    Adds urls from modules
    """
    return dash_modules_urls.send(sender=dash_modules_urls)
