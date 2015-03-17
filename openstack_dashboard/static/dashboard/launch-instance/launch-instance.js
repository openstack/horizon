(function () {
  'use strict';

  var module = angular.module('hz.dashboard.launch-instance', [ 'ngSanitize' ]);

  module.factory('launchInstanceWorkflow', [
    'dashboardBasePath',
    'dashboardWorkflow',

    function (path, dashboardWorkflow) {

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
  ]);

  // Using bootstrap-ui modal widget
  module.constant('launchInstanceWizardModalSpec', {
    backdrop: 'static',
    controller: 'ModalContainerCtrl',
    template: '<wizard ng-controller="LaunchInstanceWizardCtrl"></wizard>',
    windowClass: 'modal-dialog-wizard'
  });

  module.controller('LaunchInstanceWizardCtrl', [
    '$scope',
    'launchInstanceModel',
    'launchInstanceWorkflow',
    LaunchInstanceWizardCtrl
  ]);

  module.controller('LaunchInstanceModalCtrl', [
    '$scope',
    '$modal',
    '$window',
    'launchInstanceWizardModalSpec',
    LaunchInstanceModalCtrl
  ]);

  function LaunchInstanceWizardCtrl($scope, launchInstanceModel, launchInstanceWorkflow) {
    $scope.workflow = launchInstanceWorkflow;
    $scope.model = launchInstanceModel;
    $scope.model.initialize(true);
    $scope.submit = $scope.model.createInstance;
  }

  function LaunchInstanceModalCtrl($scope, $modal, $window, modalSpec) {
    $scope.openLaunchInstanceWizard = function (launchContext) {

      var localSpec = {
        resolve: {
          launchContext: function() { return launchContext; }
        }
      };

      angular.extend(localSpec, modalSpec);

      var launchInstanceModal = $modal.open(localSpec);

      var handleModalClose = function(redirectPropertyName) {
        return function() {
          if (launchContext && launchContext[redirectPropertyName]) {
            $window.location.href = launchContext[redirectPropertyName];
          }
        };
      };

      launchInstanceModal.result.then(handleModalClose('successUrl'),
                                      handleModalClose('dismissUrl'));

    };
  }

})();
