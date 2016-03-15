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
      info: {},
      containers: [],
      container: null,
      objects: [],
      folder: '',
      pseudo_folder_hierarchy: [],
      DELIMETER: '/',    // TODO where is this configured in the current panel

      initialize: initialize,
      selectContainer: selectContainer,
      fetchContainerDetail: fetchContainerDetail
    };

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
      return $q.all(
        swiftAPI.getContainers().then(function onContainers(data) {
          model.containers.length = 0;
          push.apply(model.containers, data.data.items);
        }),
        swiftAPI.getInfo().then(function onInfo(data) {
          model.swift_info = data.info;
        })
      );
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
        if (folder) {
          push.apply(model.pseudo_folder_hierarchy, folder.split(model.DELIMETER) || [folder]);
        }
      });
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
        return;
      }
      swiftAPI.getContainer(container.name).then(
        function success(response) {
          // copy the additional detail into the container
          angular.extend(container, response.data);

          container.is_fetched = true;

          // parse the timestamp for sensible display
          var milliseconds = Date.parse(container.timestamp);
          if (!isNaN(milliseconds)) {
            container.timestamp = new Date(milliseconds);
          }
        }
      );
    }
  }
})();
