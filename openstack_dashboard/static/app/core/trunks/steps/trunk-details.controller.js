/*
 * Copyright 2017 Ericsson
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

  /**
   * @ngdoc controller
   * @name horizon.app.core.trunks.steps.TrunkDetailsController
   * @description
   * Controller responsible for trunk attribute(s):
   *   admin_state_up
   *   description
   *   name
   * This step has to work with both create and edit actions.
   */
  angular
    .module('horizon.app.core.trunks.actions')
    .controller('TrunkDetailsController', TrunkDetailsController);

  TrunkDetailsController.$inject = [
    '$scope'
  ];

  function TrunkDetailsController($scope) {
    var ctrl = this;

    ctrl.trunkAdminStateOptions = [
      { label: gettext('Enabled'), value: true },
      { label: gettext('Disabled'), value: false }
    ];

    $scope.getTrunk.then(function(trunk) {
      ctrl.trunk = {
        admin_state_up: trunk.admin_state_up,
        description: trunk.description,
        name: trunk.name
      };

      // NOTE(bence romsics): The step controllers are naturally stateful,
      // but the actions should be stateless. However we have to
      // get back the captured user input from the step controller to the
      // action, because the action makes the neutron call. WizardController
      // helps us and passes $scope.stepModels to the actions' submit().
      // Also note that $scope.stepModels is shared between all workflow
      // steps.
      //
      // We roughly follow the example discussed and presented here:
      // http://lists.openstack.org/pipermail/openstack-dev/2016-July/099368.html
      // https://review.opendev.org/345145
      //
      // Though we deviate a bit in the use of stepModels. The example
      // has one model object per step, named after the workflow step's
      // form. Instead we treat stepModels as a generic state variable. See
      // the details below.
      //
      // The trunkSlices closures return a slice of the trunk model which
      // can be then merged by the action to get the whole trunk model. By
      // using closures we can spare the use of watchers and the constant
      // recomputation of the trunk slices even in the more complicated
      // other steps.
      $scope.stepModels.trunkSlices = $scope.stepModels.trunkSlices || {};
      $scope.stepModels.trunkSlices.getDetails = function() {
        return ctrl.trunk;
      };

      // In order to keep the update action stateless, we pass the old
      // state of the trunk down to the step controllers, then back up
      // to the update action's submit(). An alternative would be to
      // eliminate the need for the old state of the trunk at update,
      // at the price of moving the trunk diffing logic from python to
      // javascript (ie. the subports step controller).
      $scope.stepModels.initTrunk = $scope.initTrunk;

      ctrl.trunkLoaded = true;
    });

  }

})();
