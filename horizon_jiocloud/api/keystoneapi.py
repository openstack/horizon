# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright 2013 Reliance Jio Infocomm, Ltd.
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

from horizon_jiocloud.utils.utils import get_registration_service_endpoint
import requests


def create_user(data):
    endpoint = get_registration_service_endpoint()
    res = requests.post(endpoint + "/users", data=data)
    return res.json()

def activate_user(data):
    endpoint = get_registration_service_endpoint()
    user_id = data["user_id"]
    res = requests.put(endpoint + "/users/%s/activate" % (user_id), data=data)
    return res.json()

def get_user(user_id):
    endpoint = get_registration_service_endpoint()
    res = requests.get(endpoint + "/users/%s" % (user_id))
    return res.json()

def update_user(user_id, data):
    endpoint = get_registration_service_endpoint()
    res = requests.put(endpoint + "/users/%s" % (user_id), data=data)
    return res.json()

