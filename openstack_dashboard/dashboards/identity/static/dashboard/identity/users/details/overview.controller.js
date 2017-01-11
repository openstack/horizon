/*
 * (c) Copyright 2016 99Cloud
 *
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
    .module('horizon.dashboard.identity.users')
    .controller('UserOverviewController', UserOverviewController);

  UserOverviewController.$inject = [
    'horizon.dashboard.identity.users.resourceType',
    'horizon.framework.conf.resource-type-registry.service',
    '$scope'
  ];

  function UserOverviewController(
    userResourceType,
    registry,
    $scope
  ) {
    var ctrl = this;

    ctrl.user = {};
    ctrl.resourceType = registry.getResourceType(userResourceType);

    $scope.context.loadPromise.then(onGetUser);

    function onGetUser(user) {
      ctrl.user = user.data;
    }
  }

})();
