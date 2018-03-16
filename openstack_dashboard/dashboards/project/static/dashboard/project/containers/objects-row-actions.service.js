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
    .factory('horizon.dashboard.project.containers.objects-actions.delete', deleteService)
    .factory('horizon.dashboard.project.containers.objects-actions.download', downloadService)
    .factory('horizon.dashboard.project.containers.objects-actions.edit', editService)
    .factory('horizon.dashboard.project.containers.objects-actions.view', viewService)
    .factory('horizon.dashboard.project.containers.objects-actions.copy', copyService)
    .run(registerActions);

  registerActions.$inject = [
    'horizon.framework.conf.resource-type-registry.service',
    'horizon.dashboard.project.containers.object.resourceType',
    'horizon.dashboard.project.containers.objects-actions.delete',
    'horizon.dashboard.project.containers.objects-actions.download',
    'horizon.dashboard.project.containers.objects-actions.edit',
    'horizon.dashboard.project.containers.objects-actions.view',
    'horizon.dashboard.project.containers.objects-actions.copy',
    'horizon.framework.util.i18n.gettext'
  ];
  /**
   * @name registerActions
   * @description Register the row actions for objects.
   */
  function registerActions(
    registryService,
    objectResCode,
    deleteService,
    downloadService,
    editService,
    viewService,
    copyService,
    gettext
  ) {
    registryService.getResourceType(objectResCode).itemActions
    .append({
      service: downloadService,
      template: {text: gettext('Download')}
    })
    .append({
      service: viewService,
      template: {text: gettext('View Details')}
    })
    .append({
      service: editService,
      template: {text: gettext('Edit')}
    })
    .append({
      service: copyService,
      template: {text: gettext('Copy')}
    })
    .append({
      service: deleteService,
      template: {text: gettext('Delete'), type: 'delete'}
    });
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
    '$uibModal'
  ];

  function viewService(swiftAPI, basePath, model, $qExtensions, $uibModal) {
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

      $uibModal.open(localSpec);
    }
  }

  editService.$inject = [
    'horizon.app.core.openstack-service-api.swift',
    'horizon.dashboard.project.containers.basePath',
    'horizon.dashboard.project.containers.containers-model',
    'horizon.framework.util.q.extensions',
    'horizon.framework.widgets.modal-wait-spinner.service',
    'horizon.framework.widgets.toast.service',
    '$uibModal'
  ];

  function editService(swiftAPI, basePath, model, $qExtensions, modalWaitSpinnerService,
                         toastService, $uibModal) {
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
      return $uibModal.open(localSpec).result.then(editObjectCallback);
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
    '$uibModal'
  ];

  function deleteService(basePath, actionResultService, $qExtensions, $uibModal) {
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

      return $uibModal.open(localSpec).result.then(function finished() {
        return actionResultService.getActionResult().deleted(
          'OS::Swift::Object', file.name
        ).result;
      });
    }
  }

  copyService.$inject = [
    'horizon.app.core.openstack-service-api.swift',
    'horizon.dashboard.project.containers.basePath',
    'horizon.dashboard.project.containers.containerRoute',
    'horizon.dashboard.project.containers.containers-model',
    'horizon.framework.util.q.extensions',
    'horizon.framework.widgets.modal-wait-spinner.service',
    'horizon.framework.widgets.toast.service',
    '$uibModal',
    '$location'
  ];

  function copyService(swiftAPI,
                       basePath,
                       containerRoute,
                       model,
                       $qExtensions,
                       modalWaitSpinnerService,
                       toastService,
                       $uibModal,
                       $location) {
    return {
      allowed: allowed,
      perform: perform
    };

    function allowed(file) {
      var objectCheck = file.is_object;
      var capacityCheck = (file.bytes > 0);
      var result = (objectCheck && capacityCheck);
      return $qExtensions.booleanAsPromise(result);
    }

    function perform(file) {
      var localSpec = {
        backdrop: 'static',
        keyboard: false,
        controller: 'horizon.dashboard.project.containers.CopyObjectModalController as ctrl',
        templateUrl: basePath + 'copy-object-modal.html',
        resolve: {
          fileDetails: function fileDetails() {
            return {
              path: file.path,
              container: model.container.name
            };
          }
        }
      };
      return $uibModal.open(localSpec).result.then(copyObjectCallback);
    }

    function copyObjectCallback(copyInfo) {

      modalWaitSpinnerService.showModalSpinner(gettext("Copying"));
      swiftAPI.copyObject(
        model.container.name,
        copyInfo.path,
        copyInfo.dest_container,
        copyInfo.dest_name
      ).then(success, error);

      function success() {
        var dstNameArray = copyInfo.dest_name.split('/');
        dstNameArray.pop();
        var dstFolder = dstNameArray.join('/');

        modalWaitSpinnerService.hideModalSpinner();
        toastService.add(
          'success',
          interpolate(gettext('Object %(path)s has copied.'), copyInfo, true)
        );

        model.updateContainer();
        model.selectContainer(
          copyInfo.dest_container,
          dstFolder
        ).then(function openDest() {
          var path = containerRoute + copyInfo.dest_container + '/' + dstFolder;
          $location.path(path);
        });
      }

      function error() {
        modalWaitSpinnerService.hideModalSpinner();
      }
    }
  }

})();
