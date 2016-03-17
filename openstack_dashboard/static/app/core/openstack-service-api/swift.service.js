/**
 * Copyright 2015, Rackspace, US, Inc.
 *
 * Licensed under the Apache License, Version 2.0 (the 'License'); you may
 * not use this file except in compliance with the License. You may obtain
 * a copy of the License at
 *
 * http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an 'AS IS' BASIS, WITHOUT
 * WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
 * License for the specific language governing permissions and limitations
 * under the License.
 */
(function () {
  'use strict';

  angular
    .module('horizon.app.core.openstack-service-api')
    .factory('horizon.app.core.openstack-service-api.swift', swiftAPI);

  swiftAPI.$inject = [
    'horizon.framework.util.http.service',
    'horizon.framework.widgets.toast.service'
  ];

  /**
   * @ngdoc service
   * @name horizon.app.core.openstack-service-api.swift
   * @description Provides direct pass through to Swift with NO abstraction.
   */
  function swiftAPI(apiService, toastService) {
    var service = {
      copyObject: copyObject,
      createContainer: createContainer,
      createFolder: createFolder,
      deleteContainer: deleteContainer,
      deleteObject: deleteObject,
      formData: formData,
      getContainer: getContainer,
      getContainers: getContainers,
      getInfo: getInfo,
      getContainerURL: getContainerURL,
      getObjectDetails:getObjectDetails,
      getObjects: getObjects,
      getObjectURL: getObjectURL,
      setContainerAccess: setContainerAccess,
      uploadObject: uploadObject
    };

    return service;

    // this exists solely so that we can mock FormData
    function formData() {
      return new FormData();
    }

    // internal use only
    function getContainerURL(container) {
      return '/api/swift/containers/' + encodeURIComponent(container);
    }

    /**
     * @name horizon.app.core.openstack-service-api.swift.getObjectURL
     * @description
     * Calculate the download URL for an object.
     *
     */
    function getObjectURL(container, object, type) {
      var urlType = type || 'object';
      var objectUrl = encodeURIComponent(object).replace(/%2F/g, '/');
      return getContainerURL(container) + '/' + urlType + '/' + objectUrl;
    }

    /**
     * @name horizon.app.core.openstack-service-api.swift.getInfo
     * @description
     * Lists the activated capabilities for this version of the OpenStack
     * Object Storage API.
     *
     * The result is an object passed through from the Swift /info/ call.
     *
     */
    function getInfo() {
      return apiService.get('/api/swift/info/')
        .error(function () {
          toastService.add('error', gettext('Unable to get the Swift service info.'));
        });
    }

    /**
     * @name horizon.app.core.openstack-service-api.swift.getContainers
     * @description
     * Get the list of containers for this account
     *
     * The result is an object with 'items' and 'has_more' flag.
     *
     */
    function getContainers() {
      return apiService.get('/api/swift/containers/')
        .error(function() {
          toastService.add('error', gettext('Unable to get the Swift container listing.'));
        });
    }

    /**
     * @name horizon.app.core.openstack-service-api.swift.getContainer
     * @description
     * Get the container's detailed metadata
     *
     * The result is an object with the metadata fields.
     *
     */
    function getContainer(container) {
      return apiService.get(service.getContainerURL(container) + '/metadata/')
        .error(function() {
          toastService.add('error', gettext('Unable to get the container details.'));
        });
    }

    /**
     * @name horizon.app.core.openstack-service-api.swift.createContainer
     * @description
     * Creates the named container with the is_public flag set to isPublic.
     *
     */
    function createContainer(container, isPublic) {
      var data = {is_public: false};

      if (isPublic) {
        data.is_public = true;
      }
      return apiService.post(service.getContainerURL(container) + '/metadata/', data)
        .error(function (response, status) {
          if (status === 409) {
            toastService.add('error', response);
          } else {
            toastService.add('error', gettext('Unable to create the container.'));
          }
        });
    }

    /**
     * @name horizon.app.core.openstack-service-api.swift.deleteContainer
     * @description
     * Delete the named container.
     *
     */
    function deleteContainer(container) {
      return apiService.delete(service.getContainerURL(container) + '/metadata/')
        .error(function () {
          toastService.add('error', gettext('Unable to delete the container.'));
        });
    }

    /**
     * @name horizon.app.core.openstack-service-api.swift.setContainerAccess
     * @description
     * Set the container's is_public flag.
     *
     */
    function setContainerAccess(container, isPublic) {
      var data = {is_public: isPublic};

      return apiService.put(service.getContainerURL(container) + '/metadata/', data)
        .error(function () {
          toastService.add('error', gettext('Unable to change the container access.'));
        });
    }

    /**
     * @name horizon.app.core.openstack-service-api.swift.getObjects
     * @description
     * Get a listing of the objects in the container, optionally
     * limited to a specific folder.
     *
     * Use the params value "path" to specify a folder prefix to limit
     * the fetch to a pseudo-folder.
     *
     */
    function getObjects(container, params) {
      var options = {};

      if (params) {
        options.params = params;
      }

      return apiService.get(service.getContainerURL(container) + '/objects/', options)
        .error(function () {
          toastService.add('error', gettext('Unable to get the objects in container.'));
        });
    }

    /**
     * @name horizon.app.core.openstack-service-api.swift.uploadObject
     * @description
     * Add a file to the specified container with the given objectName (which
     * may include pseudo-folder path), the mimetype and raw file data.
     *
     */
    function uploadObject(container, objectName, file) {
      var fd = service.formData();
      fd.append("file", file);
      return apiService.post(
        service.getObjectURL(container, objectName),
        fd,
        {
          headers: {
            'Content-Type': undefined
          }
        }
      )
        .error(function () {
          toastService.add('error', gettext('Unable to upload the object.'));
        });
    }

    /**
     * @name horizon.app.core.openstack-service-api.swift.deleteObject
     * @description
     * Delete an object (or pseudo-folder).
     *
     */
    function deleteObject(container, objectName) {
      return apiService.delete(
        service.getObjectURL(container, objectName)
      )
        .error(function (response, status) {
          if (status === 409) {
            toastService.add('error', gettext(
              'Unable to delete the folder because it is not empty.'
            ));
          } else {
            toastService.add('error', gettext('Unable to delete the object.'));
          }
        });
    }

    /**
     * @name horizon.app.core.openstack-service-api.swift.getObjectDetails
     * @description
     * Get the metadata for an object.
     *
     */
    function getObjectDetails(container, objectName) {
      return apiService.get(
        service.getObjectURL(container, objectName, 'metadata')
      )
        .error(function () {
          toastService.add('error', gettext('Unable to get details of the object.'));
        });
    }

    /**
     * @name horizon.app.core.openstack-service-api.swift.createFolder
     * @description
     * Create a pseudo-folder.
     *
     */
    function createFolder(container, folderName) {
      return apiService.post(
        service.getObjectURL(container, folderName) + '/',
        {}
      )
        .error(function () {
          toastService.add('error', gettext('Unable to create the folder.'));
        });
    }

    /**
     * @name horizon.app.core.openstack-service-api.swift.copyObject
     * @description
     * Copy an object.
     *
     */
    function copyObject(container, objectName, destContainer, destName) {
      return apiService.post(
        service.getObjectURL(container, objectName, 'copy'),
        {dest_container: destContainer, dest_name: destName}
      )
        .error(function () {
          toastService.add('error', gettext('Unable to copy the object.'));
        });
    }
  }
}());
