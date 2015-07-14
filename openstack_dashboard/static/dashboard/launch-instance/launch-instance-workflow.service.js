/*
 *    (c) Copyright 2015 Hewlett-Packard Development Company, L.P.
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
(function () {
  'use strict';

  angular
    .module('hz.dashboard.launch-instance')
    .factory('hz.dashboard.launch-instance.workflow', launchInstanceWorkflow);

  launchInstanceWorkflow.$inject = [
    'dashboardBasePath',
    'horizon.app.core.workflow.factory'
  ];

  function launchInstanceWorkflow(path, dashboardWorkflow) {
    return dashboardWorkflow({
      title: gettext('Launch Instance'),

      steps: [
        {
          title: gettext('Select Source'),
          templateUrl: path + 'launch-instance/source/source.html',
          helpUrl: path + 'launch-instance/source/source.help.html',
          formName: 'launchInstanceSourceForm'
        },
        {
          title: gettext('Flavor'),
          templateUrl: path + 'launch-instance/flavor/flavor.html',
          helpUrl: path + 'launch-instance/flavor/flavor.help.html',
          formName: 'launchInstanceFlavorForm'
        },
        {
          title: gettext('Networks'),
          templateUrl: path + 'launch-instance/network/network.html',
          helpUrl: path + 'launch-instance/network/network.help.html',
          formName: 'launchInstanceNetworkForm',
          requiredServiceTypes: ['network']
        },
        {
          title: gettext('Security Groups'),
          templateUrl: path + 'launch-instance/security-groups/security-groups.html',
          helpUrl: path + 'launch-instance/security-groups/security-groups.help.html',
          formName: 'launchInstanceAccessAndSecurityForm'
        },
        {
          title: gettext('Key Pair'),
          templateUrl: path + 'launch-instance/keypair/keypair.html',
          helpUrl: path + 'launch-instance/keypair/keypair.help.html',
          formName: 'launchInstanceKeypairForm'
        },
        {
          title: gettext('Configuration'),
          templateUrl: path + 'launch-instance/configuration/configuration.html',
          helpUrl: path + 'launch-instance/configuration/configuration.help.html',
          formName: 'launchInstanceConfigurationForm'
        }
      ],

      btnText: {
        finish: gettext('Launch Instance')
      },

      btnIcon: {
        finish: 'fa fa-cloud-download'
      }
    });
  }

})();
