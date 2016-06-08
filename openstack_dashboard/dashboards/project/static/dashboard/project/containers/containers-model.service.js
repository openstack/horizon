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
    'horizon.framework.util.http.service',
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
  function ContainersModel(swiftAPI, apiService, $q) {
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
      updateContainer: updateContainer,
      recursiveCollect: recursiveCollect,
      recursiveDelete: recursiveDelete,
      getContainers: getContainers,

      _recursiveDeleteFiles: recursiveDeleteFiles,
      _recursiveDeleteFolders: recursiveDeleteFolders
    };

    // keep a handle on this promise so that controllers can resolve on the
    // initialisation completing (i.e. containers listing loaded)
    model.intialiseDeferred = $q.defer();

    model.getContainersDeferred = $q.defer();

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
        spec.path = encodeURIComponent(folder) + model.DELIMETER;
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

    /**
     * @ngdoc method
     * @name ContainersModel.recursiveCollect
     * @returns {promise}
     *
     * @description
     * Recursively collect the names of files and folders under a
     * folder listing. Each item in the listing will be an object
     * retrieved from swift's getObjects() call.
     *
     * The promise will resolve once the recursion is complete.
     *
     * The result array will be populated with file path strings
     * or objects with folder name and another array of contents:
     *
     *     [
     *       'file name',
     *       'another file',
     *       {
     *         folder: 'path/of/folder',
     *         tree: [
     *           {
     *             folder: 'path/of/folder/empty',
     *             tree: []
     *           },
     *           'more files'
     *         ]
     *       }
     *     ]
     *
     * The state object holds a count that should be updated for
     * each file found, and a cancel sentinel that can be used to
     * stop recursion.
     *
     * This is invoked by the DeleteObjectsModalController.
     *
     * This is intended to be a first step in recursive deletion.
     */
    function recursiveCollect(state, items, result) {
      return $q.all(items.map(function each(item) {
        if (item.is_object) {
          state.counted.files++;
          result.push(item.path);
          return null;
        } else {
          var folder = {folder: item.path, tree: []};
          if (state.cancel) {
            return null;
          }
          result.push(folder);
          state.counted.folders++;
          var spec = {
            delimiter: model.DELIMETER,
            path: encodeURIComponent(item.path).replace(/%2F/g, '/')
          };
          return swiftAPI.getObjects(model.container.name, spec)
            .then(function objects(response) {
              return recursiveCollect(state, response.data.items, folder.tree);
            });
        }
      }));
    }

    /**
     * @ngdoc method
     * @name ContainersModel.recursiveDelete
     * @returns {promise}
     *
     * @description
     * Recursively delete a tree of swift files, with "node" being
     * the tree specification from recursiveCollect.
     *
     * The state object holds a delete counts that should be updated
     * for each file/folder/failure deleted.
     *
     * We first delete all files and then delete the folders in a
     * structured manner to avoid the "not empty" error.
     *
     * Note that we fire off all the deletes here; browsers automatically
     * throttle HTTP calls for us.
     */
    function recursiveDelete(state, node) {
      return model._recursiveDeleteFiles(state, node).then(function () {
        return model._recursiveDeleteFolders(state, node);
      });
    }

    // Just delete the files
    function recursiveDeleteFiles(state, node) {
      if (angular.isObject(node)) {
        return $q.all(node.tree.map(function each(subnode) {
          return recursiveDeleteFiles(state, subnode);
        }));
      } else {
        return swiftAPI.deleteObject(model.container.name, node).then(
          function done() { state.deleted.files++; });
      }
    }

    // Just delete the folders, but do so "serially" so there's no chance
    // of "not empty" conflict
    // Note that we call through to the delete without the usual toast-on-error
    function recursiveDeleteFolders(state, node) {
      if (!angular.isObject(node)) {
        return null;
      }
      if (!node.tree.length) {
        return deleteFolder(node.folder);
      }

      function deleteFolder(folderName) {
        if (angular.isUndefined(folderName)) {
          return null;
        }
        var path = folderName + model.DELIMETER;
        var url = swiftAPI.getObjectURL(model.container.name, path);
        return apiService.delete(url).then(done, fail);

        function done() {
          state.deleted.folders++;
        }

        // custom error handling to ignore 404 for pseudo-folders that have been deleted
        // because pseudo-folders gonna pseudo folder (in short, deleting a pseudo-folder
        // a/b/c will *most likely* remove the pseudo-folders a and b from existence
        // also).
        function fail(response) {
          if (response.status === 404) {
            // the pseudo-folder this path belongs to has already been deleted
            done();
          } else {
            // some other failure
            state.deleted.failures++;
          }
        }
      }

      return $q.all(node.tree.map(function each(subnode) {
        // first recurse so we do the leaves first
        return recursiveDeleteFolders(state, subnode);
      })).then(function then() {
        return deleteFolder(node.folder);
      });
    }

    /**
     * @ngdoc method
     * @name ContainersModel.getContainers
     *
     * @param {Object} params Search parameters for filtering
     * @description
     * Gets the model containers filtered by the given query. If query is empty
     * then it returns all of the containers
     *
       */
    function getContainers(params) {
      swiftAPI.getContainers(params).then(function onContainers(data) {
        model.containers.length = 0;
        push.apply(model.containers, data.data.items);
      }).then(function resolve() {
        model.getContainersDeferred.resolve();
      });
    }

  }
})();
