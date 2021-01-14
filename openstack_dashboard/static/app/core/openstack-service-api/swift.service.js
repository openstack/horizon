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
   * @name swiftAPI
   * @param {Object} apiService
   * @param {Object} toastService
   * @description Provides direct pass through to Swift with NO abstraction.
   * @returns {Object} The service
   */
  function swiftAPI(apiService, toastService) {
    var service = {
      copyObject: copyObject,
      createContainer: createContainer,
      createFolder: createFolder,
      deleteContainer: deleteContainer,
      deleteObject: deleteObject,
      getContainer: getContainer,
      getContainers: getContainers,
      getInfo: getInfo,
      getContainerURL: getContainerURL,
      getObjectDetails:getObjectDetails,
      getObjects: getObjects,
      getObjectURL: getObjectURL,
      getPolicyDetails: getPolicyDetails,
      setContainerAccess: setContainerAccess,
      uploadObject: uploadObject
    };

    return service;

    // internal use only
    function getContainerURL(container) {
      return '/api/swift/containers/' + encodeURIComponent(container);
    }

    /**
     * @name getObjectURL
     * @param {Object} container - A container name
     * @param {Object} object - The object to be encoded
     * @param {string} type - String representation of the type
     * @description
     * Calculate the download URL for an object.
     * @returns {string} A URL that represents the given object
     */
    function getObjectURL(container, object, type) {
      var urlType = type || 'object';
      var objectUrl = encodeURIComponent(object).replace(/%2F/g, '/');
      return getContainerURL(container) + '/' + urlType + '/' + objectUrl;
    }

    /**
     * @name getInfo
     * @description
     * Lists the activated capabilities for this version of the OpenStack
     * Object Storage API.
     *
     * @returns {Object} The result of the object passed to the Swift /info/ call.
     *
     */
    function getInfo() {
      return apiService.get('/api/swift/info/')
        .error(function () {
          toastService.add('error', gettext('Unable to get the Swift service info.'));
        });
    }

    /**
     * @name getPolicyDetails
     * @description
     * Fetch all the storage policy details with display names and storage values.
     *
     * @returns {Object} The result of the object passed to the Swift /policies call.
     *
     */
    function getPolicyDetails() {
      return apiService.get('/api/swift/policies/').error(function() {
        toastService.add(
          'error',
          gettext('Unable to fetch the policy details.')
        );
      });
    }

    /**
     * @name getContainers
     * @description
     * Get the list of containers for this account
     *
     * @returns {Object} An object with 'items' and 'has_more' flag.
     *
     */
    function getContainers(params) {
      var config = params ? {'params': params} : {};
      return apiService.get('/api/swift/containers/', config)
        .error(function() {
          toastService.add('error', gettext('Unable to get the Swift container listing.'));
        });
    }

    /**
     * @name getContainer
     * @param {Object} container - The container
     * @description
     * Get the container's detailed metadata
     *
     * If you just wish to test for the existence of the container, set
     * ignoreError so user-visible error isn't automatically displayed.
     * @returns {Object} An object with the metadata fields.
     *
     */
    function getContainer(container, ignoreError) {
      var promise = apiService.get(service.getContainerURL(container) + '/metadata/');
      if (ignoreError) {
        return promise.error(angular.noop);
      }
      return promise.error(function() {
        toastService.add('error', gettext('Unable to get the container details.'));
      });
    }

    /**
     * @name createContainer
     * @param {Object} container - The container
     * @param {boolean} isPublic - Whether the container should be public
     * @param {string} policy - The storage policy for the container.
     * @description
     * Creates the named container with the is_public flag set to isPublic.
     * @returns {Object} The result of the creation call
     *
     */
    function createContainer(container, isPublic, policy) {
      var data = {is_public: false, storage_policy: policy};

      if (isPublic) {
        data.is_public = true;
      }
      return apiService.post(service.getContainerURL(container) + '/metadata/', data)
        .error(function (response) {
          if (response.status === 409) {
            toastService.add('error', response);
          } else {
            toastService.add('error', gettext('Unable to create the container.'));
          }
        });
    }

    /**
     * @name deleteContainer
     * @param {Object} container - The container to delete
     * @description
     * Delete the named container.
     * @returns {Object} The result of the delete call
     *
     */
    function deleteContainer(container) {
      return apiService.delete(service.getContainerURL(container) + '/metadata/')
        .error(function (response, status) {
          if (status === 409) {
            toastService.add('error', response);
          } else {
            toastService.add('error', gettext('Unable to delete the container.'));
          }
        });
    }

    /**
     * @name setContainerAccess
     * @param {Object} container - The container
     * @param {boolean} isPublic - Whether the container should be public
     * @description
     * Set the container's is_public flag.
     * @returns {Object} The result of the access call
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
     * @name getObjects
     * @param {Object} container - The container
     * @param {Object} params - The parameters to pass to the call
     * @description
     * Get a listing of the objects in the container, optionally
     * limited to a specific folder.
     *
     * Use the params value "path" to specify a folder prefix to limit
     * the fetch to a pseudo-folder.
     * @returns {Object} The result of the API call
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
     * @name uploadObject
     * @param {Object} container - The container
     * @param {string} objectName - The object's name (and optional path)
     * @param {Object} file - File data
     * @description
     * Add or replace a file in the specified container with the given objectName
     * (which may include pseudo-folder path), the mimetype and raw file data.
     * @returns {Object} The result of the API call
     *
     */
    function uploadObject(container, objectName, file) {
      return apiService.post(
        service.getObjectURL(container, objectName),
        {file: file}
      )
        .error(function () {
          toastService.add('error', gettext('Unable to upload the object.'));
        });
    }

    /**
     * @name deleteObject
     * @param {Object} container - The container
     * @param {string} objectName - The name of the object to delete
     * @description
     * Delete an object (or pseudo-folder). Note that pseudo-folder
     * names *must* end in a DELIMETER ("/" usually).
     * @returns {Object} The result of the API call
     *
     */
    function deleteObject(container, objectName) {
      return apiService.delete(
        service.getObjectURL(container, objectName)
      )
        .error(function (response) {
          if (response.status === 409) {
            toastService.add('error', gettext(
              'Unable to delete the folder because it is not empty.'
            ));
          } else {
            toastService.add('error', gettext('Unable to delete the object.'));
          }
        });
    }

    /**
     * @name getObjectDetails
     * @param {Object} container - The container
     * @param {string} objectName - The name of the object to get info about
     * @description
     * Get the metadata for an object.
     *
     * If you just wish to test for the existence of the object, set
     * ignoreError so user-visible error isn't automatically displayed.
     * @returns {Object} The result of the API call
     *
     */
    function getObjectDetails(container, objectName, ignoreError) {
      var promise = apiService.get(
        service.getObjectURL(container, objectName, 'metadata')
      );
      if (ignoreError) {
        // provide a noop error handler so the error is ignored
        return promise.error(angular.noop);
      }
      return promise.error(function () {
        toastService.add('error', gettext('Unable to get details of the object.'));
      });
    }

    /**
     * @name createFolder
     * @param {Object} container - The container
     * @param {string} folderName - The new folder name
     * @description
     * Create a pseudo-folder.
     * @returns {Object} The result of the API call
     *
     */
    function createFolder(container, folderName) {
      return apiService.post(
        service.getObjectURL(container, folderName) + '/',
        {}
      )
        .error(function (response, status) {
          if (status === 409) {
            toastService.add('error', response);
          } else {
            toastService.add('error', gettext('Unable to create the folder.'));
          }
        });
    }

    /**
     * @name copyObject
     * @param {Object} container - The original container
     * @param {string} objectName - The original object's name
     * @param {Object} destContainer - The destination container
     * @param {string} destName - The destination object's name
     * @description
     * Copy an object.
     * @returns {Object} The result of the API call
     *
     */
    function copyObject(container, objectName, destContainer, destName) {
      return apiService.post(
        service.getObjectURL(container, objectName, 'copy'),
        {dest_container: destContainer, dest_name: destName}
      )
        .error(function (response, status) {
          if (status === 409) {
            toastService.add('error', response);
          } else {
            toastService.add('error', gettext('Unable to copy the object.'));
          }
        });
    }
  }
}());
