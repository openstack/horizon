/*
 * Copyright 2017 Ericsson
 *
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
  "use strict";

  angular
    .module('horizon.app.core.trunks')
    .controller('TrunkOverviewController', TrunkOverviewController);

  TrunkOverviewController.$inject = [
    'horizon.app.core.trunks.resourceType',
    'horizon.framework.conf.resource-type-registry.service',
    'horizon.app.core.openstack-service-api.userSession',
    'horizon.app.core.trunks.service',
    '$scope'
  ];

  function TrunkOverviewController(
    trunkResourceTypeCode,
    registry,
    userSession,
    trunksService,
    $scope
  ) {
    var ctrl = this;

    ctrl.resourceType = registry.getResourceType(trunkResourceTypeCode);
    ctrl.tableConfig = {
      selectAll: false,
      expand: false,
      trackId: 'segmentation_id',
      /*
       * getTableColumns here won't work as that will give back the
       * columns for trunk, but here we need columns only for the
       * subports, which is a (list of) dictionary(ies) in the
       * trunk dictionary.
       */
      columns: [
        {id: 'segmentation_type', title: gettext('Segmentation Type'),
         priority: 1, sortDefault: true},
        {id: 'segmentation_id', title: gettext('Segmentation ID'),
         priority: 1, sortDefault: true},
        {id: 'port_id', title: gettext('Port ID'), priority: 1,
         urlFunction: trunksService.getPortDetailsPath}
      ]
    };

    $scope.context.loadPromise.then(onGetTrunk);

    function onGetTrunk(trunk) {
      ctrl.trunk = trunk.data;

      userSession.get().then(setProject);

      function setProject(session) {
        ctrl.projectId = session.project_id;
      }
    }
  }

})();
