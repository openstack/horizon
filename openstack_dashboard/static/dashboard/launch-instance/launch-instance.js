(function () {
  'use strict';

  var module = angular.module('hz.dashboard.launch-instance', []);

  module.factory('launchInstanceWorkflow', ['dashboardBasePath', function (path) {

    return {
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
          title: gettext('Network'),
          templateUrl: path + 'launch-instance/network/network.html',
          helpUrl: path + 'launch-instance/network/network.help.html',
          formName: 'launchInstanceNetworkForm'
        },
        {
          title: gettext('Access and Security'),
          templateUrl: path + 'launch-instance/access-and-security/access-and-security.html',
          helpUrl: path + 'launch-instance/access-and-security/access-and-security.help.html',
          formName: 'launchInstanceAccessAndSecurityForm'
        },
        {
          title: gettext('Post Creation'),
          templateUrl: path + 'launch-instance/post-creation/post-creation.html',
          helpUrl: path + 'launch-instance/post-creation/post-creation.help.html',
          formName: 'launchInstancePostCreationForm'
        }
      ],

      btnText: {
        finish: gettext('Launch Instance')
      },

      btnIcon: {
        finish: 'fa fa-cloud-download'
      }
    };
  }]);

  // Using bootstrap-ui modal widget
  module.constant('launchInstanceWizardModalSpec', {
    backdrop: 'static',
    controller: 'ModalContainerCtrl',
    template: '<wizard ng-controller="LaunchInstanceWizardCtrl"></wizard>',
    windowClass: 'modal-dialog-wizard'
  });

  module.controller('LaunchInstanceWizardCtrl', [
    '$scope',
    '$q', // temporary, should call api access services
    'launchInstanceWorkflow',
    LaunchInstanceWizardCtrl
  ]);

  module.controller('LaunchInstanceModalCtrl', [
    '$scope',
    '$modal',
    'launchInstanceWizardModalSpec',
    LaunchInstanceModalCtrl
  ]);

  function LaunchInstanceWizardCtrl($scope, $q, launchInstanceWorkflow) {
    $scope.workflow = launchInstanceWorkflow;
    $scope.model = {
      source: {},
      flavor: {},
      network: {},
      accessAndSecurity: {},
      postCreation: {}
    };
    $scope.submit = function () {
      return $q(function (resolve) {
        //
        // emulating server side process
        //
        setTimeout(function () {
          resolve();
        }, 1000);
      });
    };
  }

  function LaunchInstanceModalCtrl($scope, $modal, modalSpec) {
    $scope.openLaunchInstanceWizard = function () {
      $modal.open(modalSpec);
    };
  }

})();
