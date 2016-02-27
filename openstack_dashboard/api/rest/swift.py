# Copyright 2015, Rackspace, US, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""API for the swift service.
"""

from django import forms
from django.views.decorators.csrf import csrf_exempt
from django.views import generic

from openstack_dashboard import api
from openstack_dashboard.api.rest import urls
from openstack_dashboard.api.rest import utils as rest_utils


@urls.register
class Info(generic.View):
    """API for information about the Swift installation.
    """
    url_regex = r'swift/info/$'

    @rest_utils.ajax()
    def get(self, request):
        """Get information about the Swift installation.
        """
        capabilities = api.swift.swift_get_capabilities(request)
        return {'info': capabilities}


@urls.register
class Containers(generic.View):
    """API for swift container listing for an account
    """
    url_regex = r'swift/containers/$'

    @rest_utils.ajax()
    def get(self, request):
        """Get the list of containers for this account

        TODO(neillc): Add pagination
        """
        containers, has_more = api.swift.swift_get_containers(request)
        containers = [container.to_dict() for container in containers]
        return {'items': containers, 'has_more': has_more}


@urls.register
class Container(generic.View):
    """API for swift container level information
    """

    url_regex = r'swift/containers/(?P<container>[^/]+)/metadata/$'

    @rest_utils.ajax()
    def get(self, request, container):
        """Get the container details
        """
        return api.swift.swift_get_container(request, container).to_dict()

    @rest_utils.ajax()
    def post(self, request, container):
        metadata = {}

        if 'is_public' in request.DATA:
            metadata['is_public'] = request.DATA['is_public']

        api.swift.swift_create_container(request, container, metadata=metadata)
        return rest_utils.CreatedResponse(
            u'/api/swift/containers/%s' % container,
        )

    @rest_utils.ajax()
    def delete(self, request, container):
        api.swift.swift_delete_container(request, container)

    @rest_utils.ajax(data_required=True)
    def put(self, request, container):
        metadata = {'is_public': request.DATA['is_public']}
        api.swift.swift_update_container(request, container, metadata=metadata)


@urls.register
class Objects(generic.View):
    """API for a list of swift objects
    """
    url_regex = r'swift/containers/(?P<container>[^/]+)/objects/$'

    @rest_utils.ajax()
    def get(self, request, container):
        """Get object information.

        :param request:
        :param container:
        :return:
        """
        path = request.GET.get('path')

        objects = api.swift.swift_get_objects(
            request,
            container,
            prefix=path
        )

        # filter out the folder from the listing if we're filtering for
        # contents of a (pseudo) folder
        contents = [{
            'path': o.name,
            'name': o.name.split('/')[-1],
            'bytes': o.bytes,
            'is_subdir': o.content_type == 'application/pseudo-folder',
            'is_object': o.content_type != 'application/pseudo-folder',
            'content_type': o.content_type
        } for o in objects[0] if o.name != path]
        return {'items': contents}


class UploadObjectForm(forms.Form):
    file = forms.FileField(required=False)


@urls.register
class Object(generic.View):
    """API for a single swift object or pseudo-folder
    """
    url_regex = r'swift/containers/(?P<container>[^/]+)/object/' \
        '(?P<object_name>.+)$'

    # note: not an AJAX request - the body will be raw file content
    @csrf_exempt
    def post(self, request, container, object_name):
        """Create a new object or pseudo-folder

        :param request:
        :param container:
        :param object_name:

        If the object_name (ie. POST path) ends in a '/' then a folder is
        created, rather than an object. Any file content passed along with
        the request will be ignored in that case.

        POST parameter:

        :param file: the file data for the upload.

        :return:
        """
        form = UploadObjectForm(request.POST, request.FILES)
        if not form.is_valid():
            raise rest_utils.AjaxError(500, 'Invalid request')

        data = form.clean()

        if object_name[-1] == '/':
            result = api.swift.swift_create_pseudo_folder(
                request,
                container,
                object_name
            )
        else:
            result = api.swift.swift_upload_object(
                request,
                container,
                object_name,
                data['file']
            )

        return rest_utils.CreatedResponse(
            u'/api/swift/containers/%s/object/%s' % (container, result.name)
        )

    @rest_utils.ajax()
    def delete(self, request, container, object_name):
        api.swift.swift_delete_object(request, container, object_name)


@urls.register
class ObjectMetadata(generic.View):
    """API for a single swift object
    """
    url_regex = r'swift/containers/(?P<container>[^/]+)/metadata/' \
        '(?P<object_name>.+)$'

    @rest_utils.ajax()
    def get(self, request, container, object_name):
        return api.swift.swift_get_object(
            request,
            container_name=container,
            object_name=object_name,
            with_data=False
        ).to_dict()


@urls.register
class ObjectCopy(generic.View):
    """API to copy a swift object
    """
    url_regex = r'swift/containers/(?P<container>[^/]+)/copy/' \
        '(?P<object_name>.+)$'

    @rest_utils.ajax()
    def post(self, request, container, object_name):
        dest_container = request.DATA['dest_container']
        dest_name = request.DATA['dest_name']
        result = api.swift.swift_copy_object(
            request,
            container,
            object_name,
            dest_container,
            dest_name
        )
        return rest_utils.CreatedResponse(
            u'/api/swift/containers/%s/object/%s' % (dest_container,
                                                     result.name)
        )
