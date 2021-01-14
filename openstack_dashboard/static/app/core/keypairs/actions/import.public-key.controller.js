/**
 * Licensed under the Apache License, Version 2.0 (the "License"); you may
 * not use this file except in compliance with the License. You may obtain
 * a copy of the License at
 *
 *    http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
 * WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
 * License for the specific language governing permissions and limitations
 * under the License.
 */

(function() {
  'use strict';

  /**
   * @ngdoc controller
   * @name horizon.app.core.keypairs.actions.ImportPublicKeyController
   * @ngController
   *
   * @description
   * Controller for the loading public key file
   */
  angular
    .module('horizon.app.core.keypairs.actions')
    .controller('horizon.app.core.keypairs.actions.ImportPublicKeyController',
      importPublicKeyController);

  importPublicKeyController.$inject = [
    '$scope'
  ];

  function importPublicKeyController($scope) {
    var ctrl = this;
    ctrl.title = $scope.schema.properties.public_key.title;
    ctrl.key_types = {
      'ssh': gettext("SSH Key"),
      'x509': gettext("X509 Certificate")
    };
    ctrl.public_key = "";
    ctrl.onKeyTypeChange = function (keyType) {
      $scope.model.key_type = keyType;
    };
    ctrl.onPublicKeyChange = function (publicKey) {
      $scope.model.public_key = publicKey;
    };
  }
})();
