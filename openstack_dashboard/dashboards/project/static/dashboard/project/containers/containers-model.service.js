/*
 *    (c) Copyright 2015 Rackspace US, Inc
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *    http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */
(function () {
  'use strict';

  var push = Array.prototype.push;

  /**
   * @ngdoc overview
   * @name horizon.dashboard.project.containers
   *
   * @description
   * Provide a model for the display of containers.
   */

  angular
    .module('horizon.dashboard.project.containers')
    .factory('horizon.dashboard.project.containers.containers-model', ContainersModel);

  ContainersModel.$inject = [
    'horizon.app.core.openstack-service-api.swift',
    '$q'
  ];

  /**
   * @ngdoc service
   * @name ContainersModel
   *
   * @description
   * This is responsible for providing data to the containers
   * interface. It is also the center point of communication
   * between the UI and services API.
   */
  function ContainersModel(swiftAPI, $q) {
    var model = {
      info: {},           // swift installation information
      containers: [],     // all containers for this account
      container: null,    // current active container
      objects: [],        // current objects list (active container)
      folder: '',         // current folder path
      pseudo_folder_hierarchy: [],
      DELIMETER: '/',    // TODO where is this configured in the current panel

      initialize: initialize,
      selectContainer: selectContainer,
      fullPath: fullPath,
      fetchContainerDetail: fetchContainerDetail,
      deleteObject: deleteObject,
      updateContainer: updateContainer
    };

    // keep a handle on this promise so that controllers can resolve on the
    // initialisation completing (i.e. containers listing loaded)
    model.intialiseDeferred = $q.defer();

    return model;

    /**
     * @ngdoc method
     * @name ContainersModel.initialize
     * @returns {promise}
     *
     * @description
     * Send request to get data to initialize the model.
     */
    function initialize() {
      $q.all([
        swiftAPI.getContainers().then(function onContainers(data) {
          model.containers.length = 0;
          push.apply(model.containers, data.data.items);
        }),
        swiftAPI.getInfo().then(function onInfo(data) {
          model.swift_info = data.info;
        })
      ]).then(function resolve() {
        model.intialiseDeferred.resolve();
      });
    }

    /**
     * @ngdoc method
     * @name ContainersModel.selectContainer
     * @returns {promise}
     *
     * @description
     * Sets the currently active container and subfolder path, and
     * fetches the object listing. Returns the promise for the object
     * listing fetch.
     */
    function selectContainer(name, folder) {
      for (var i = 0; i < model.containers.length; i++) {
        if (model.containers[i].name === name) {
          model.container = model.containers[i];
          break;
        }
      }
      model.objects.length = 0;
      model.pseudo_folder_hierarchy.length = 0;
      model.folder = folder;

      var spec = {
        delimiter: model.DELIMETER
      };
      if (folder) {
        spec.path = folder + model.DELIMETER;
      }

      return swiftAPI.getObjects(name, spec).then(function onObjects(response) {
        push.apply(model.objects, response.data.items);
        // generate the download URL for each file
        angular.forEach(model.objects, function setId(object) {
          object.url = swiftAPI.getObjectURL(name, model.fullPath(object.name));
        });
        if (folder) {
          push.apply(model.pseudo_folder_hierarchy, folder.split(model.DELIMETER) || [folder]);
        }
      });
    }

    /**
     * @ngdoc method
     * @name ContainersModel.fullPath
     * @returns string
     *
     * @description
     * Determine the full path name for a given file name, by prepending the
     * current folder, if any.
     */
    function fullPath(name) {
      if (model.folder) {
        return model.folder + model.DELIMETER + name;
      }
      return name;
    }

    /**
     * @ngdoc method
     * @name ContainersModel.updateContainer
     * @returns {promise}
     *
     * @description
     * Update the active container using fetchContainerDetail (forced).
     *
     */
    function updateContainer() {
      return model.fetchContainerDetail(model.container, true);
    }

    /**
     * @ngdoc method
     * @name ContainersModel.fetchContainerDetail
     * @returns {promise}
     *
     * @description
     * Fetch the detailed information about a container (beyond its name,
     * contents count and byte size fetched in the containers listing).
     *
     * The timestamp will be converted from the ISO string to a Javascript Date.
     */
    function fetchContainerDetail(container, force) {
      // only fetch if we haven't already
      if (container.is_fetched && !force) {
        var deferred = $q.defer();
        deferred.resolve();
        return deferred.promise;
      }
      return swiftAPI.getContainer(container.name).then(
        function success(response) {
          // copy the additional detail into the container
          angular.extend(container, response.data);

          // copy over the swift-renamed attributes
          container.bytes = parseInt(container.container_bytes_used, 10);
          container.count = parseInt(container.container_object_count, 10);

          container.is_fetched = true;

          // parse the timestamp for sensible display
          var milliseconds = Date.parse(container.timestamp);
          if (!isNaN(milliseconds)) {
            container.timestamp = new Date(milliseconds);
          }
        }
      );
    }

    /**
     * @ngdoc method
     * @name ContainersModel.deleteObject
     * @returns {promise}
     *
     * @description
     * Delete an object in the currently selected container.
     */
    function deleteObject(object) {
      var path = model.fullPath(object.name);
      if (object.is_subdir) {
        path += model.DELIMETER;
      }
      return swiftAPI.deleteObject(model.container.name, path).then(
        function success() {
          for (var i = model.objects.length - 1; i >= 0; i--) {
            if (model.objects[i].name === object.name) {
              model.objects.splice(i, 1);
            }
          }
        });
    }
  }
})();
