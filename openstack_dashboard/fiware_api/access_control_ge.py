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

import logging
import requests
from django.template.loader import render_to_string

LOG = logging.getLogger('idm_logger')

# TODO(garcianavalon) extract as conf options
AC_URL = 'https://az.testbed.fi-ware.eu/authzforce/\
        domains/f764202c-fc7a-11e2-8cc3-fa163e3515ad/pap/policySet'
XACML_TEMPLATE = 'access_control/policy_set.xacml'
SSL_CERTIFICATE= 'TODO'

def policies_update(roles_permisions):
    """Gets all role's permissions and generates a xacml file to
    update the Access Control.
    """
    context = {
        'policy_set_description': 'TODO',
        'roles': roles_permisions,
    }
    xml = render_to_string(XACML_TEMPLATE, context)
    LOG.debug('Created new XACML {0}'.format(xml))

def policy_delete(role_id):
    LOG.debug('Deleting role {0} from AC GE'.format(role_id))
    return delete(role_id)

def put(xml):
    
    # POST the data to the AC GE
    headers = {
        'content-type': 'application/xml'
    }
    response = requests.put(AC_URL, 
                            data=xml, 
                            headers=headers,
                            cert=SSL_CERTIFICATE)
    LOG.debug('Response code from the AC GE: {0}'.format(
                                        response.status_code))
    return response

def delete(role_id):
    # TODO(garcianavalon) send the id
    response = requests.delete(AC_URL, 
                            cert=SSL_CERTIFICATE)
    LOG.debug('Response code from the AC GE: {0}'.format(
                                        response.status_code))
    return response