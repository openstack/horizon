/*
 *    (c) Copyright 2016 Red Hat, Inc.
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
   * @name LaunchInstanceNetworkPortController
   * @description
   * Controller for the Launch Instance - Network Step.
   */
  angular
    .module('horizon.dashboard.project.workflow.launch-instance')
    .controller('LaunchInstanceNetworkPortController', LaunchInstanceNetworkPortController);

  LaunchInstanceNetworkPortController.$inject = [
    'horizon.dashboard.project.workflow.launch-instance.basePath',
    'launchInstanceModel',
    'horizon.framework.widgets.action-list.button-tooltip.row-warning.service'
  ];

  function LaunchInstanceNetworkPortController(basePath, launchInstanceModel, tooltipService) {
    var ctrl = this;

    ctrl.portStatuses = {
      'ACTIVE': gettext('Active'),
      'DOWN': gettext('Down')
    };

    ctrl.portAdminStates = {
      'UP': gettext('Up'),
      'DOWN': gettext('Down')
    };

    ctrl.vnicTypes = {
      'normal': gettext('Normal'),
      'direct': gettext('Direct'),
      'direct-physical': gettext('Direct Physical'),
      'macvtap': gettext('MacVTap'),
      'baremetal': gettext('Bare Metal'),
      'virtio-forwarder': gettext('Virtio Forwarder')
    };

    function getPortStatus(status) {
      return ctrl.portStatuses[status];
    }

    function getPortAdminState(state) {
      return ctrl.portAdminStates[state];
    }

    var portsArr = launchInstanceModel.ports;
    ctrl.portsObj = {};
    ctrl.isPortsObjGenerated = false;

    function getNameOrID(id) {
      ctrl.portsObj = ctrl.getPortsObj(portsArr);
      var port = ctrl.portsObj[id];
      return ctrl.nameOrID(port);
    }

    function getPortFixedIPs(id) {
      var port = ctrl.portsObj[id];
      var fixedIPs = '';
      for (var ip in port.subnet_names) {
        fixedIPs += ip + ' on subnet ' + port.subnet_names[ip] + '\n';
      }
      return fixedIPs;
    }

    ctrl.tableDataMulti = {
      available: launchInstanceModel.ports,
      allocated: launchInstanceModel.newInstanceSpec.ports
    };

    ctrl.availableTableConfig = {
      selectAll: false,
      trackId: 'id',
      detailsTemplateUrl: basePath + 'networkports/port-details.html',
      columns: [
        {id: 'id', title: gettext('Name'), priority: 1, filters: [getNameOrID]},
        {id: 'id', title: gettext('IP'), priority: 2, filters: [getPortFixedIPs]},
        {id: 'admin_state', title: gettext('Admin State'), priority: 2,
         filters: [getPortAdminState]},
        {id: 'status', title: gettext('Status'), priority: 2, filters: [getPortStatus]}
      ]
    };

    ctrl.allocatedTableConfig = angular.copy(ctrl.availableTableConfig);
    ctrl.allocatedTableConfig.noItemsMessage = gettext(
      'Select one or more ports from the available ports below.');

    ctrl.tableHelpText = {
      availHelpText: gettext('Select one or more')
    };

    ctrl.filterFacets = [{
      label: gettext('Name'),
      name: 'name',
      singleton: true
    }, {
      label: gettext('ID'),
      name: 'id',
      singleton: true
    }, {
      label: gettext('Admin State'),
      name: 'admin_state',
      singleton: true
    }, {
      label: gettext('Status'),
      name: 'status',
      singleton: true
    }];

    ctrl.tableLimits = {
      maxAllocation: -1
    };

    ctrl.tooltipModel = tooltipService;

    ctrl.nameOrID = function nameOrId(data) {
      return angular.isDefined(data.name) && data.name !== '' ? data.name : data.id;
    };

    ctrl.getPortsObj = function (data) {
      if (!ctrl.isPortsObjGenerated) {
        var ports = data.reduce(function (acc, cur) {
          acc[cur.id] = cur;
          return acc;
        }, {});
        ctrl.isPortsObjGenerated = true;
        return ports;
      }
      else { return ctrl.portsObj; }
    };
  }
})();
