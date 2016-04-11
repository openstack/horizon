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

  /**
   * @ngdoc controller
   *
   * @name horizon.dashboard.project.containers.ObjectsController
   *
   * @description
   * Controller for the interface around the objects in a single container.
   */
  angular
    .module('horizon.dashboard.project.containers')
    .controller('horizon.dashboard.project.containers.ObjectsController', ObjectsController);

  ObjectsController.$inject = [
    'horizon.app.core.openstack-service-api.swift',
    'horizon.dashboard.project.containers.containers-model',
    'horizon.dashboard.project.containers.containerRoute',
    'horizon.dashboard.project.containers.basePath',
    'horizon.dashboard.project.containers.objects-row-actions',
    'horizon.framework.widgets.modal-wait-spinner.service',
    'horizon.framework.widgets.modal.simple-modal.service',
    'horizon.framework.widgets.toast.service',
    '$modal',
    '$q',
    '$routeParams'
  ];

  function ObjectsController(swiftAPI, containersModel, containerRoute, basePath, rowActions,
                             modalWaitSpinnerService, simpleModalService, toastService,
                             $modal, $q, $routeParams)
  {
    var ctrl = this;

    ctrl.rowActions = rowActions;
    ctrl.model = containersModel;
    ctrl.selected = {};
    ctrl.numSelected = 0;

    ctrl.containerURL = containerRoute + encodeURIComponent($routeParams.container) +
      ctrl.model.DELIMETER;
    if (angular.isDefined($routeParams.folder)) {
      ctrl.currentURL = ctrl.containerURL + encodeURIComponent($routeParams.folder) +
        ctrl.model.DELIMETER;
    } else {
      ctrl.currentURL = ctrl.containerURL;
    }

    ctrl.breadcrumbs = [];

    // ensure that the base model data is loaded and then run our path-based
    // container selection
    ctrl.model.intialiseDeferred.promise.then(function afterInitialise() {
      ctrl.model.selectContainer($routeParams.container, $routeParams.folder)
        .then(function then() {
          ctrl.breadcrumbs = ctrl.getBreadcrumbs();
        });
    });

    ctrl.anySelectable = anySelectable;
    ctrl.isSelected = isSelected;
    ctrl.selectAll = selectAll;
    ctrl.clearSelected = clearSelected;
    ctrl.toggleSelect = toggleSelect;
    ctrl.deleteSelected = deleteSelected;
    ctrl.deleteSelectedAction = deleteSelectedAction;
    ctrl.createFolder = createFolder;
    ctrl.createFolderCallback = createFolderCallback;
    ctrl.getBreadcrumbs = getBreadcrumbs;
    ctrl.objectURL = objectURL;
    ctrl.uploadObject = uploadObject;
    ctrl.uploadObjectCallback = uploadObjectCallback;

    //////////

    function anySelectable() {
      for (var i = 0; i < ctrl.model.objects.length; i++) {
        if (ctrl.model.objects[i].is_object) {
          return true;
        }
      }
      return false;
    }

    function isSelected(file) {
      if (!file.is_object) {
        return false;
      }
      var state = ctrl.selected[file.name];
      return angular.isDefined(state) && state.checked;
    }

    function selectAll() {
      ctrl.clearSelected();
      angular.forEach(ctrl.model.objects, function each(file) {
        if (file.is_object) {
          ctrl.selected[file.name] = {checked: true, file: file};
          ctrl.numSelected++;
        }
      });
    }

    function clearSelected() {
      ctrl.selected = {};
      ctrl.numSelected = 0;
    }

    function toggleSelect(file) {
      if (!file.is_object) {
        return;
      }
      var checkedState = !ctrl.isSelected(file);
      ctrl.selected[file.name] = {
        checked: checkedState,
        file: file
      };
      if (checkedState) {
        ctrl.numSelected++;
      } else {
        ctrl.numSelected--;
      }
    }

    function getBreadcrumbs() {
      var crumbs = [];
      var encoded = ctrl.model.pseudo_folder_hierarchy.map(encodeURIComponent);
      for (var i = 0; i < encoded.length; i++) {
        crumbs.push({
          label: ctrl.model.pseudo_folder_hierarchy[i],
          url: ctrl.containerURL + encoded.slice(0, i + 1).join(ctrl.model.DELIMETER)
        });
      }
      return crumbs;
    }

    function objectURL(file) {
      return ctrl.currentURL + encodeURIComponent(file.name);
    }

    function deleteSelected() {
      var options = {
        title: gettext('Confirm Delete'),
        body: interpolate(
          gettext('Are you sure you want to delete %(numSelected)s files?'),
          ctrl, true
        ),
        submit: gettext('Yes'),
        cancel: gettext('No')
      };
      simpleModalService.modal(options).result.then(function confirmed() {
        return ctrl.deleteSelectedAction();
      });
    }

    function deleteSelectedAction() {
      var promises = [];
      angular.forEach(ctrl.selected, function deleteObject(item) {
        promises.push(ctrl.model.deleteObject(item.file));
      });
      modalWaitSpinnerService.showModalSpinner(gettext("Deleting"));
      function clean() {
        modalWaitSpinnerService.hideModalSpinner();
        ctrl.clearSelected();
        ctrl.model.updateContainer();
      }
      $q.all(promises).then(function success() {
        clean();
        toastService.add('success', gettext('Deleted.'));
      }, function fail() {
        clean();
        toastService.add('error', gettext('Failed to delete.'));
      });
    }

    function uploadModal(html) {
      var localSpec = {
        backdrop: 'static',
        controller: 'UploadObjectModalController as ctrl',
        templateUrl: basePath + html
      };

      return $modal.open(localSpec).result;
    }

    function createFolder() {
      uploadModal('create-folder-modal.html').then(ctrl.createFolderCallback);
    }

    function createFolderCallback(name) {
      swiftAPI.createFolder(
        ctrl.model.container.name,
        ctrl.model.fullPath(name))
      .then(
        function success() {
          toastService.add(
            'success',
            interpolate(gettext('Folder %(name)s created.'), {name: name}, true)
          );
          ctrl.model.updateContainer();
          // TODO optimize me
          ctrl.model.selectContainer(
            ctrl.model.container.name,
            ctrl.model.folder
          );
        }
      );
    }

    // TODO consider https://github.com/nervgh/angular-file-upload
    function uploadObject() {
      uploadModal('upload-object-modal.html').then(ctrl.uploadObjectCallback);
    }

    function uploadObjectCallback(info) {
      modalWaitSpinnerService.showModalSpinner(gettext("Uploading"));
      swiftAPI.uploadObject(
        ctrl.model.container.name,
        ctrl.model.fullPath(info.name),
        info.upload_file
      ).then(function success() {
        modalWaitSpinnerService.hideModalSpinner();
        toastService.add(
          'success',
          interpolate(gettext('File %(name)s uploaded.'), info, true)
        );
        ctrl.model.updateContainer();
        // TODO optimize me
        ctrl.model.selectContainer(
          ctrl.model.container.name,
          ctrl.model.folder
        );
      }, function error() {
        modalWaitSpinnerService.hideModalSpinner();
      });
    }
  }
})();
