/*
 *    (c) Copyright 2016 Rackspace US, Inc
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

(function() {
  'use strict';

  angular
    .module('horizon.dashboard.project.containers')
    .factory('horizon.dashboard.project.containers.objects-row-actions', rowActions)
    .factory('horizon.dashboard.project.containers.objects-actions.delete', deleteService)
    .factory('horizon.dashboard.project.containers.objects-actions.download', downloadService)
    .factory('horizon.dashboard.project.containers.objects-actions.view', viewService);

  rowActions.$inject = [
    'horizon.dashboard.project.containers.basePath',
    'horizon.dashboard.project.containers.objects-actions.delete',
    'horizon.dashboard.project.containers.objects-actions.download',
    'horizon.dashboard.project.containers.objects-actions.view',
    'horizon.framework.util.i18n.gettext'
  ];

  /**
   * @ngdoc factory
   * @name horizon.app.core.images.table.row-actions.service
   * @description A list of row actions.
   */
  function rowActions(
    basePath,
    deleteService,
    downloadService,
    viewService,
    gettext
  ) {
    return {
      actions: actions
    };

    ///////////////

    function actions() {
      return [
        {
          service: downloadService,
          template: {text: gettext('Download')}
        },
        {
          service: viewService,
          template: {text: gettext('View Details')}
        },
        {
          service: deleteService,
          template: {text: gettext('Delete'), type: 'delete'}
        }
      ];
    }
  }

  downloadService.$inject = [
    'horizon.framework.util.q.extensions',
    '$window'
  ];

  function downloadService($qExtensions, $window) {
    return {
      allowed: function allowed(file) { return $qExtensions.booleanAsPromise(file.is_object); },
      // remove leading url slash to ensure uses relative link/base path
      // thus using webroot.
      perform: function perform(file) {
        $window.location.href = file.url.replace(/^\//, '');
      }
    };
  }

  viewService.$inject = [
    'horizon.app.core.openstack-service-api.swift',
    'horizon.dashboard.project.containers.basePath',
    'horizon.dashboard.project.containers.containers-model',
    'horizon.framework.util.q.extensions',
    '$modal'
  ];

  function viewService(swiftAPI, basePath, model, $qExtensions, $modal) {
    return {
      allowed: function allowed(file) {
        return $qExtensions.booleanAsPromise(file.is_object);
      },
      perform: function perform(file) {
        var objectPromise = swiftAPI.getObjectDetails(
          model.container.name,
          model.fullPath(file.name)
        ).then(
          function received(response) {
            return response.data;
          }
        );
        var localSpec = {
          backdrop: 'static',
          controller: 'SimpleModalController as ctrl',
          templateUrl: basePath + 'object-details-modal.html',
          resolve: {
            context: function context() { return objectPromise; }
          }
        };

        $modal.open(localSpec);
      }
    };
  }

  deleteService.$inject = [
    'horizon.dashboard.project.containers.basePath',
    '$modal',
    'horizon.dashboard.project.containers.containers-model',
    'horizon.framework.util.q.extensions'
  ];

  function deleteService(basePath, $modal, model, $qExtensions) {
    return {
      allowed: function allowed() {
        return $qExtensions.booleanAsPromise(true);
      },
      perform: function perform(file) {
        var localSpec = {
          backdrop: 'static',
          controller: 'DeleteObjectsModalController as ctrl',
          templateUrl: basePath + 'delete-objects-modal.html',
          resolve: {
            selected: function () {
              return [{checked: true, file: file}];
            }
          }
        };

        return $modal.open(localSpec).result.then(function finished() {
          // remove the deleted file/folder from display
          for (var i = model.objects.length - 1; i >= 0; i--) {
            if (model.objects[i].name === file.name) {
              model.objects.splice(i, 1);
              break;
            }
          }
          model.updateContainer();
        });
      }
    };
  }
})();
