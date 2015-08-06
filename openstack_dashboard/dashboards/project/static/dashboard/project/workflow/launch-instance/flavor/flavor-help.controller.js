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
    .controller('LaunchInstanceFlavorHelpController', LaunchInstanceFlavorHelpController);

  function LaunchInstanceFlavorHelpController() {
    var ctrl = this;

    ctrl.title = gettext('Flavor Help');

    ctrl.paragraphs = [
      /*eslint-disable max-len */
      gettext('The flavor you select for an instance determines the amount of compute, storage and memory resources that will be carved out for the instance.'),
      gettext('The flavor you select must have enough resources allocated to support the type of instance you are trying to create. Flavors that don\'t provide enough resources for your instance are identified on the <b>Available</b> table with a yellow warning icon.'),
      gettext('Administrators are responsible for creating and managing flavors. A custom flavor can be created for you or for a specific project where it is shared with the users assigned to that project. If you need a custom flavor, contact your administrator.')
      /*eslint-enable max-len */
    ];
  }

})();
