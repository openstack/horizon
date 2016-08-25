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
    .factory('horizon.dashboard.project.containers.objects-actions.edit', editService)
    .factory('horizon.dashboard.project.containers.objects-actions.view', viewService);

  rowActions.$inject = [
    'horizon.dashboard.project.containers.objects-actions.delete',
    'horizon.dashboard.project.containers.objects-actions.download',
    'horizon.dashboard.project.containers.objects-actions.edit',
    'horizon.dashboard.project.containers.objects-actions.view',
    'horizon.framework.util.i18n.gettext'
  ];
  /**
   * @ngdoc factory
   * @name horizon.app.core.images.table.row-actions.service
   * @description A list of row actions.
   */
  function rowActions(
    deleteService,
    downloadService,
    editService,
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
          service: editService,
          template: {text: gettext('Edit')}
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
      allowed: allowed,
      perform: perform
    };

    function allowed(file) {
      return $qExtensions.booleanAsPromise(file.is_object);
    }

    // remove leading url slash to ensure uses relative link/base path
    // thus using webroot.
    function perform(file) {
      $window.location.href = file.url.replace(/^\//, '');
    }
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
      allowed: allowed,
      perform: perform
    };

    function allowed(file) {
      return $qExtensions.booleanAsPromise(file.is_object);
    }

    function perform(file) {
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
  }

  editService.$inject = [
    'horizon.app.core.openstack-service-api.swift',
    'horizon.dashboard.project.containers.basePath',
    'horizon.dashboard.project.containers.containers-model',
    'horizon.framework.util.q.extensions',
    'horizon.framework.widgets.modal-wait-spinner.service',
    'horizon.framework.widgets.toast.service',
    '$modal'
  ];

  function editService(swiftAPI, basePath, model, $qExtensions, modalWaitSpinnerService,
                         toastService, $modal) {
    return {
      allowed: allowed,
      perform: perform
    };

    function allowed(file) {
      return $qExtensions.booleanAsPromise(file.is_object);
    }

    function perform(file) {
      var localSpec = {
        backdrop: 'static',
        controller: 'horizon.dashboard.project.containers.EditObjectModalController as ctrl',
        templateUrl: basePath + 'edit-object-modal.html',
        resolve: {
          fileDetails: function fileDetails() {
            return {
              path: file.path,
              container: model.container.name
            };
          }
        }
      };
      return $modal.open(localSpec).result.then(editObjectCallback);
    }

    function editObjectCallback(uploadInfo) {
      modalWaitSpinnerService.showModalSpinner(gettext("Uploading"));
      swiftAPI.uploadObject(
        model.container.name,
        uploadInfo.path,
        uploadInfo.edit_file
      ).then(success, error);

      function success() {
        modalWaitSpinnerService.hideModalSpinner();
        toastService.add(
          'success',
          interpolate(gettext('File %(path)s uploaded.'), uploadInfo, true)
        );
        model.updateContainer();
        model.selectContainer(
          model.container.name,
          model.folder
        );
      }

      function error() {
        modalWaitSpinnerService.hideModalSpinner();
      }
    }
  }

  deleteService.$inject = [
    'horizon.dashboard.project.containers.basePath',
    'horizon.framework.util.actions.action-result.service',
    'horizon.framework.util.q.extensions',
    '$modal'
  ];

  function deleteService(basePath, actionResultService, $qExtensions, $modal) {
    return {
      allowed: allowed,
      perform: perform
    };

    function allowed() {
      return $qExtensions.booleanAsPromise(true);
    }

    function perform(file) {
      var localSpec = {
        backdrop: 'static',
        controller: 'DeleteObjectsModalController as ctrl',
        templateUrl: basePath + 'delete-objects-modal.html',
        resolve: {
          selected: function () {
            return [file];
          }
        }
      };

      return $modal.open(localSpec).result.then(function finished() {
        return actionResultService.getActionResult().deleted(
          'OS::Swift::Object', file.name
        ).result;
      });
    }
  }
})();
