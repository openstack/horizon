/**
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
  'use strict';

  angular
    .module('horizon.dashboard.admin.flavors')
    .controller('FlavorsTableController', FlavorsTableController);

  FlavorsTableController.$inject = [
    'horizon.app.core.openstack-service-api.nova'
  ];

  /**
   * @ngdoc FlavorsTableController
   * @ngController
   *
   * @description
   * Controller for the flavors panel.
   * Serves as the focal point for table actions.
   */
  function FlavorsTableController(
    nova
  ) {
    var ctrl = this;

    ctrl.flavors = [];
    ctrl.iflavors = [];

    ctrl.searchFacets = getSearchFacets();

    init();

    ////////////////////////////////

    function init() {
      nova.getFlavors(true, true).then(onGetFlavors);
    }

    function onGetFlavors(response) {
      ctrl.flavors = response.data.items;
    }

    function getSearchFacets() {
      return [
        {
          label: gettext('Name'),
          name: 'name',
          singleton: true
        },
        {
          label: gettext('VCPUs'),
          name: 'vcpus',
          singleton: true
        },
        {
          label: gettext('RAM'),
          name: 'ram',
          singleton: true
        },
        {
          label: gettext('Public'),
          name: 'os-flavor-access:is_public',
          singleton: true,
          options: [
            {label: gettext('Yes'), key: 'true'},
            {label: gettext('No'), key: 'false'}
          ]
        }
      ];
    }

  }
})();
