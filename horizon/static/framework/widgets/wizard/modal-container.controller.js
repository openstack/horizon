/*
 *    (c) Copyright 2015 Hewlett-Packard Development Company, L.P.
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
    .module('horizon.framework.widgets.wizard')
    .controller('ModalContainerController', ModalContainerController);

  ModalContainerController.$inject = ['$scope', '$modalInstance', 'launchContext'];

  /**
   * @ngdoc controller
   * @name horizon.framework.widgets.wizard.controller:ModalContainerController
   * @description
   * Extends the bootstrap-ui modal widget
   */
  function ModalContainerController($scope, $modalInstance, launchContext) {
    // $scope is used because the methods are shared between
    // wizard and modal-container controller
    /*eslint-disable angular/controller-as */
    $scope.launchContext = launchContext;
    $scope.close = function(args) {
      $modalInstance.close(args);
    };
    $scope.cancel = function() {
      $modalInstance.dismiss();
    };
    /*eslint-enable angular/controller-as */
  }
})();
