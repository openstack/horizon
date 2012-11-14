from __future__ import absolute_import

import logging
import urlparse
import urllib2
import json

from openstack_dashboard.api.base import url_for

LOG = logging.getLogger(__name__)

def imagefactory_request(request, body, path):
    imagefactory_url = urlparse.urlparse(url_for(request, 'image-build'))

    imagefactory_request = urllib2.Request(imagefactory_url + path)
    imagefactory_request.add_header('Content-type', 'application/json')
    imagefactory_request.add_header('Accept', 'application/json')
    imagefactory_request.add_data(json.dumps(body))
    return urllib2.urlopen(imagefactory_request)

def create_image(template, request):
    body = { "provider_image": { "template":template,
                                 "target":"openstack-kvm",
                                 # A bug in Imagefactory requires us to set provider information as a string
                                 "provider":"""{\"glance-host\":\"192.168.122.104\",
                                                \"glance-port\": 9292 }""",
                                  # FIXME Get proper user credentials and auth_url from request/keystone
                                 "credentials":"""<provider_credentials>
                                                      <openstack_credentials>
                                                          <username>admin</username>
                                                          <tenant>admin</tenant>
                                                          <password>verybadpass</password>
                                                          <strategy>keystone</strategy>
                                                          <auth_url>http://192.168.122.104:5000/v2.0</auth_url>
                                                      </openstack_credentials>
                                                  </provider_credentials>"""}}
    return imagefactory_request(request, body, "/provider_images")
