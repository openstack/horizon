/*
 * Licensed under the Apache License, Version 2.0 (the 'License');
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *    http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an 'AS IS' BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */
(function() {
  "use strict";

  angular
    .module('horizon.app.core.keypairs')
    .controller('horizon.app.core.keypairs.DetailsController', KeypairDetailsController);

  KeypairDetailsController.$inject = ['$scope'];

  function KeypairDetailsController($scope) {
    var ctrl = this;
    ctrl.keypair = {};

    $scope.context.loadPromise.then(onGetKeypair);

    function onGetKeypair(response) {
      ctrl.keypair = response.data;
      ctrl.keypair.keypair_id = ctrl.keypair.id;
      ctrl.keypair.id = ctrl.keypair.name;
    }
  }
})();
