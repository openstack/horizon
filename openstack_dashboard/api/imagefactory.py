from __future__ import absolute_import

import logging
import urlparse
import urllib2
import json
import xml.etree.ElementTree as ET

from openstack_dashboard.api.base import url_for

LOG = logging.getLogger(__name__)

class FactoryImage:
    def __init__(self, data):
        self.id = data['id']
        self.glance_id = data['identifier_on_provider']
        self.target_image = data['target_image']
        self.status = data['status']
        self.progress = data['percent_complete']

        if data['template']:
            try:
                print data['template']
                template = ET.fromstring(data['template'])
                self.template = template.find("./name").text
                self.name = template.find("./name").text
                self.os_name = template.find("./os/name").text + " v" + template.find("./os/version").text
                self.os_version = template.find("./os/version").text
                self.arch = template.find("./os/arch").text
                self.description = template.find("./description").text
            except:
                LOG.error("Unable to parse Template")

def imagefactory_request(request, path, body=None, method=None):
    LOG.debug('Looking up Imagefactory entrypoint URL')
    imagefactory_url = urlparse.urlparse(url_for(request, "image-build"))

    imagefactory_request = urllib2.Request(imagefactory_url.geturl() + path)
    imagefactory_request.add_header('Content-type', 'application/json')
    imagefactory_request.add_header('Accept', 'application/json')
    if body:
      imagefactory_request.add_data(json.dumps(body))

    if method:
        request.get_method = lambda: method

    return urllib2.urlopen(imagefactory_request)

def image_create(request, template):
    LOG.debug('Creating Image Create request for Imagefactory')
    glance_url = urlparse.urlparse(url_for(request, "image"))
    keystone_url = urlparse.urlparse(url_for(request, "identity"))
    body = { "provider_image": { "template":template,
                                 "target":"openstack-kvm",
                                 # We must set this as a string rather than a dict
                                 "provider":"""{\"glance-host\":\"192.168.122.104\",
                                                \"glance-port\": 9292 }""",
                                 "credentials":"""<provider_credentials>
                                                      <openstack_credentials>
                                                          <username>admin</username>
                                                          <tenant>admin</tenant>
                                                          <password>verybadpass</password>
                                                          <strategy>keystone</strategy>
                                                          <auth_url>http://192.168.122.104:5000/v2.0</auth_url>
                                                      </openstack_credentials>
                                                  </provider_credentials>"""}}
    return imagefactory_request(request, "/provider_images", body)

def image_get(request, image_id):
    response = json.loads(imagefactory_request(request, "/provider_images/" + image_id).read)
    return FactoryImage(response)

def image_delete(request, image_id):
    response = json.loads(imagefactory_request(request, "/provider_images/" + image_id).read)
    return FactoryImage(response)

def image_list(request):
    images = []
    list = json.loads(imagefactory_request(request, "/provider_images").read())
    for i in list["provider_images"]:
        response = imagefactory_request(request, "/provider_images/" + i['provider_image']['id']).read()
        image = FactoryImage(json.loads(response)['provider_image'])
        images.append(image)
    return images