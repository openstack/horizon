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
    .factory('horizon.dashboard.project.containers.objects-batch-actions.create-folder',
             createFolderService)
    .factory('horizon.dashboard.project.containers.objects-batch-actions.delete', deleteService)
    .factory('horizon.dashboard.project.containers.objects-batch-actions.upload', uploadService)
    .run(registerActions);

  registerActions.$inject = [
    'horizon.framework.conf.resource-type-registry.service',
    'horizon.dashboard.project.containers.object.resourceType',
    'horizon.dashboard.project.containers.objects-batch-actions.create-folder',
    'horizon.dashboard.project.containers.objects-batch-actions.delete',
    'horizon.dashboard.project.containers.objects-batch-actions.upload'
  ];

  /**
   * @name registerActions
   * @description Register batch and global actions.
   */
  function registerActions(
    registryService,
    objectResCode,
    createFolderService,
    deleteService,
    uploadService
  ) {
    registryService.getResourceType(objectResCode).batchActions
    .append({
      service: uploadService,
      template: {text: '<span class="fa fa-upload"></span>'}
    })
    .append({
      service: createFolderService,
      template: {text: '<span class="fa fa-plus"></span>&nbsp;' + gettext('Folder')}
    })
    .append({
      service: deleteService,
      template: {text: '', type: 'delete-selected'}
    });
  }

  function uploadModal(html, $uibModal) {
    var localSpec = {
      backdrop: 'static',
      controller: 'horizon.dashboard.project.containers.UploadObjectModalController as ctrl',
      templateUrl: html
    };
    return $uibModal.open(localSpec).result;
  }

  uploadService.$inject = [
    'horizon.app.core.openstack-service-api.swift',
    'horizon.dashboard.project.containers.basePath',
    'horizon.dashboard.project.containers.containers-model',
    'horizon.framework.util.q.extensions',
    'horizon.framework.widgets.modal-wait-spinner.service',
    'horizon.framework.widgets.toast.service',
    '$uibModal'
  ];

  function uploadService(swiftAPI, basePath, model, $qExtensions, modalWaitSpinnerService,
                         toastService, $uibModal) {
    var service = {
      allowed: function allowed() {
        return $qExtensions.booleanAsPromise(true);
      },
      perform: function perform() {
        uploadModal(basePath + 'upload-object-modal.html', $uibModal)
          .then(service.uploadObjectCallback);
      },
      uploadObjectCallback: uploadObjectCallback
    };
    return service;

    function uploadObjectCallback(uploadInfo) {
      modalWaitSpinnerService.showModalSpinner(gettext("Uploading"));
      swiftAPI.uploadObject(
        model.container.name,
        model.fullPath(uploadInfo.name),
        uploadInfo.upload_file
      ).then(function success() {
        modalWaitSpinnerService.hideModalSpinner();
        toastService.add(
          'success',
          interpolate(gettext('File %(name)s uploaded.'), uploadInfo, true)
        );
        model.updateContainer();
        model.selectContainer(
          model.container.name,
          model.folder
        );
      }, function error() {
        modalWaitSpinnerService.hideModalSpinner();
      });
    }
  }

  createFolderService.$inject = [
    'horizon.app.core.openstack-service-api.swift',
    'horizon.dashboard.project.containers.basePath',
    'horizon.dashboard.project.containers.containers-model',
    'horizon.framework.util.q.extensions',
    'horizon.framework.widgets.toast.service',
    '$uibModal'
  ];

  function createFolderService(swiftAPI, basePath, model, $qExtensions, toastService, $uibModal) {
    var service = {
      allowed: function allowed() {
        return $qExtensions.booleanAsPromise(true);
      },
      perform: function perform() {
        uploadModal(basePath + 'create-folder-modal.html', $uibModal)
          .then(service.createFolderCallback);
      },
      createFolderCallback: createFolderCallback
    };
    return service;

    function createFolderCallback(name) {
      swiftAPI.createFolder(
        model.container.name,
        model.fullPath(name))
        .then(
          function success() {
            toastService.add(
              'success',
              interpolate(gettext('Folder %(name)s created.'), {name: name}, true)
            );
            model.updateContainer();
            model.selectContainer(
              model.container.name,
              model.folder
            );
          }
        );
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
      allowed: function allowed() {
        return $qExtensions.booleanAsPromise(true);
      },
      perform: function perform(files) {
        var localSpec = {
          backdrop: 'static',
          controller: 'DeleteObjectsModalController as ctrl',
          templateUrl: basePath + 'delete-objects-modal.html',
          resolve: {
            selected: function () {
              return files;
            }
          }
        };

        return $uibModal.open(localSpec).result.then(function finished() {
          return actionResultService.getActionResult().deleted(
            'OS::Swift::Object', 'DELETED'
          ).result;
        });
      }
    };
  }
})();
