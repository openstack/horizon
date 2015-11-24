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
    .module('horizon.dashboard.project.workflow.launch-instance')
    .factory('horizon.dashboard.project.workflow.launch-instance.workflow', launchInstanceWorkflow);

  launchInstanceWorkflow.$inject = [
    'horizon.dashboard.project.workflow.launch-instance.basePath',
    'horizon.app.core.workflow.factory'
  ];

  function launchInstanceWorkflow(basePath, dashboardWorkflow) {
    return dashboardWorkflow({
      title: gettext('Launch Instance'),

      steps: [
        {
          id: 'details',
          title: gettext('Details'),
          templateUrl: basePath + 'details/details.html',
          helpUrl: basePath + 'details/details.help.html',
          formName: 'launchInstanceDetailsForm'
        },
        {
          id: 'source',
          title: gettext('Source'),
          templateUrl: basePath + 'source/source.html',
          helpUrl: basePath + 'source/source.help.html',
          formName: 'launchInstanceSourceForm'
        },
        {
          id: 'flavor',
          title: gettext('Flavor'),
          templateUrl: basePath + 'flavor/flavor.html',
          helpUrl: basePath + 'flavor/flavor.help.html',
          formName: 'launchInstanceFlavorForm'
        },
        {
          id: 'networks',
          title: gettext('Networks'),
          templateUrl: basePath + 'network/network.html',
          helpUrl: basePath + 'network/network.help.html',
          formName: 'launchInstanceNetworkForm',
          requiredServiceTypes: ['network']
        },
        {
          id: 'secgroups',
          title: gettext('Security Groups'),
          templateUrl: basePath + 'security-groups/security-groups.html',
          helpUrl: basePath + 'security-groups/security-groups.help.html',
          formName: 'launchInstanceAccessAndSecurityForm'
        },
        {
          id: 'keypair',
          title: gettext('Key Pair'),
          templateUrl: basePath + 'keypair/keypair.html',
          helpUrl: basePath + 'keypair/keypair.help.html',
          formName: 'launchInstanceKeypairForm'
        },
        {
          id: 'configuration',
          title: gettext('Configuration'),
          templateUrl: basePath + 'configuration/configuration.html',
          helpUrl: basePath + 'configuration/configuration.help.html',
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
