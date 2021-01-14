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

(function () {
  'use strict';

  angular
    .module('horizon.dashboard.project.workflow.launch-instance')
    .controller('LaunchInstanceImportKeyPairController', LaunchInstanceImportKeyPairController);

  LaunchInstanceImportKeyPairController.$inject = [
    '$uibModalInstance',
    'horizon.app.core.openstack-service-api.nova',
    'horizon.framework.widgets.toast.service',
    'horizon.dashboard.project.workflow.launch-instance.basePath'
  ];

  /**
   * @ngdoc controller
   * @name LaunchInstanceImportKeyPairController
   * @param {Object} $uibModalInstance
   * @param {Object} novaAPI
   * @param {Object} toastService
   * @param {string} basePath
   * @description
   * Provide a dialog for import of an existing ssh public key.
   * @returns {undefined} Returns nothing
   */
  function LaunchInstanceImportKeyPairController($uibModalInstance, novaAPI,
                                                 toastService, basePath) {
    var ctrl = this;

    ctrl.submit = submit;
    ctrl.cancel = cancel;
    ctrl.model = { name: '', public_key: '', key_type: 'ssh' };
    ctrl.path = basePath + 'keypair/';
    ctrl.title = gettext('Public Key');
    ctrl.key_types = {
      'ssh': gettext("SSH Key"),
      'x509': gettext("X509 Certificate")
    };

    ctrl.onKeyTypeChange = function (keyType) {
      ctrl.model.key_type = keyType;
    };
    //////////

    function submit() {
      novaAPI.createKeypair(ctrl.model).then(successCallback);
    }

    function successCallback(data) {
      $uibModalInstance.close(data.data);

      var successMsg = gettext('Successfully imported key pair %(name)s.');
      toastService.add('success', interpolate(successMsg, { name: data.data.name }, true));
    }

    function cancel() {
      $uibModalInstance.dismiss();
    }
  }

})();
