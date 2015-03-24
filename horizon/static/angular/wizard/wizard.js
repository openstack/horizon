(function () {
  'use strict';

  angular.module('hz.widget.wizard', ['ui.bootstrap'])

    .constant('wizardLabels', {
      cancel: gettext('Cancel'),
      back: gettext('Back'),
      next: gettext('Next'),
      finish: gettext('Finish')
    })

    .directive('wizard', ['basePath', function (path) {
      return {
        controller: ['$scope', 'wizardLabels', function ($scope, wizardLabels) {
          $scope.currentIndex = 0;
          $scope.openHelp = false;
          $scope.workflow = $scope.workflow || {};
          $scope.btnText = angular.extend({}, wizardLabels, $scope.workflow.btnText);
          $scope.btnIcon = $scope.workflow.btnIcon || {};
          $scope.steps = $scope.workflow.steps || [];
          $scope.wizardForm = {};
          $scope.showSpinner = false;
          $scope.hasError = false;
          $scope.switchTo = function (index) {
            $scope.currentIndex = index;
            $scope.openHelp = false;
          };
          $scope.showError = function (errorMessage) {
            $scope.showSpinner = false;
            $scope.errorMessage = errorMessage;
            $scope.hasError = true;
          };
        }],
        templateUrl: path + 'wizard/wizard.html'
      };
    }])

    .controller('ModalContainerCtrl', ['$scope', '$modalInstance', 'launchContext', function ($scope, $modalInstance, launchContext) {
        $scope.launchContext = launchContext;
        $scope.close = function () {
          $modalInstance.close();
        };
        $scope.cancel = function () {
          $modalInstance.dismiss();
        };
      }
    ]);

})();
