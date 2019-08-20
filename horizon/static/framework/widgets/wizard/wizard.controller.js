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
(function() {
  'use strict';

  var extend = angular.extend;
  var forEach = angular.forEach;

  angular
    .module('horizon.framework.widgets.wizard')
    .controller('WizardController', WizardController);

  WizardController.$inject = [
    '$scope',
    '$q',
    'horizon.framework.widgets.wizard.labels',
    'horizon.framework.widgets.wizard.events',
    'horizon.framework.events'
  ];

  /**
    * @ngdoc controller
    * @name horizon.framework.widgets.wizard.controller:WizardController
    * @description
    * Controller used by 'wizard'
    */
  function WizardController($scope, $q, wizardLabels, wizardEvents, frameworkEvents) {
    var ctrl = this;
    var viewModel = $scope.viewModel = {};
    var initTask = $q.defer();

    /*eslint-disable angular/controller-as */
    $scope.initPromise = initTask.promise;
    $scope.currentIndex = -1;
    $scope.workflow = $scope.workflow || {};
    if ($scope.workflow.initControllers) {
      $scope.workflow.initControllers($scope);
    }
    var steps = $scope.steps = $scope.workflow.steps || [];
    $scope.wizardForm = {};

    // a place to keep each step's captured data, named for their step.formName
    $scope.stepModels = {};

    $scope.switchTo = switchTo;
    $scope.showError = showError;
    ctrl.toggleHelpBtn = toggleHelpBtn;
    ctrl.onInitSuccess = onInitSuccess;
    ctrl.onInitError = onInitError;

    /*eslint-enable angular/controller-as */

    viewModel.btnText = extend({}, wizardLabels, $scope.workflow.btnText);
    viewModel.btnIcon = $scope.workflow.btnIcon || {};
    viewModel.showSpinner = false;
    viewModel.hasError = false;
    viewModel.onClickFinishBtn = onClickFinishBtn;
    viewModel.isSubmitting = false;

    $scope.initPromise.then(onInitSuccess, onInitError);

    checkAllReadiness().finally(function() {
      initTask.resolve();
      viewModel.ready = true;
      switchToFirstReadyStep();
    });

    //////////

    function switchTo(index) {
      /**
       * In each step's controller, $scope.$index can be used by the step
       * to identify itself. For example:
       *
       * var comingToMe = (event.to === $scope.$index);
       */
      $scope.$broadcast(wizardEvents.ON_SWITCH, {
        from: $scope.currentIndex,
        to: index
      });
      ctrl.toggleHelpBtn(index);
      /*eslint-disable angular/controller-as */
      $scope.currentIndex = index;
      $scope.openHelp = false;
      /*eslint-enable angular/controller-as*/
    }

    function showError(errorMessage) {
      viewModel.showSpinner = false;
      viewModel.hasError = true;
      if (errorMessage && angular.isString(errorMessage.data)) {
        viewModel.errorMessage = errorMessage.data;
      } else {
        viewModel.errorMessage = errorMessage;
      }
      viewModel.isSubmitting = false;
    }

    function beforeSubmit() {
      $scope.$broadcast(wizardEvents.BEFORE_SUBMIT);
    }

    function afterSubmit(args) {
      $scope.$broadcast(wizardEvents.AFTER_SUBMIT);
      /*eslint-disable angular/controller-as */
      $scope.close(args);
      /*eslint-enable angular/controller-as */
    }

    function onClickFinishBtn() {
      // prevent the finish button from being clicked again
      viewModel.isSubmitting = true;
      beforeSubmit();
      $scope.submit($scope.stepModels).then(afterSubmit, showError);
    }

    function onInitSuccess() {
      if (viewModel.hasError) {
        return;
      }

      $scope.$broadcast(wizardEvents.ON_INIT_SUCCESS);
      if (steps.length > 0) {
        ctrl.toggleHelpBtn(0);
      }
    }

    function onInitError() {
      $scope.$broadcast(wizardEvents.ON_INIT_ERROR);
    }

    $scope.$on(frameworkEvents.AUTH_ERROR, function(evt, arg) {
      viewModel.hasError = true;
      viewModel.errorMessage = arg;
      return;
    });

    function toggleHelpBtn(index) {
      // Toggle help icon button if a step's helpUrl is not defined
      if (angular.isUndefined(steps[index].helpUrl)) {
        $scope.hideHelpBtn = true;
      } else {
        $scope.hideHelpBtn = false;
      }
    }

    /**
     * Each step in the workflow can provide an optional `checkReadiness`
     * method, which should return a promise. When this method is provided
     * with a step, the `.ready` property of the step will be set to
     * `false` until the promise gets resolved. If no `checkReadiness` method
     * is provided, the `.ready` property of the step will be set to `true`
     * by default.
     *
     * This is useful for workflows where some steps are optional and/or
     * displayed to the UI conditionally, and the check for the condition
     * is an asynchronous operation.
     *
     * @return {Promise} This promise gets resolved when all the checking
     * for each step's promises are done.
     *
     * @example

      ```js
        var launchInstanceWorkFlow = {
          //...
          steps: [
            // ...
            {
              title: gettext('Network'),
              templateUrl: path + 'launch-instance/network/network.html',
              helpUrl: path + 'launch-instance/network/network.help.html',
              formName: 'launchInstanceNetworkForm',

              checkReadiness: function() {
                var d = $q.defer();
                setTimeout(function() {
                  d.resolve();
                }, 500);
                return d.promise;
              }
            }
            //...
          ],
          //...
        };
      ```
     */
    function checkAllReadiness() {
      var stepReadyPromises = [];

      forEach(steps, function(step) {
        step.ready = !step.checkReadiness;

        if (step.checkReadiness) {
          var promise = step.checkReadiness();
          stepReadyPromises.push(promise);
          promise.then(function(isReady) {
            step.ready = isReady;
          });
        }
      });

      viewModel.ready = stepReadyPromises.length === 0;
      return $q.all(stepReadyPromises).finally(function() {
        $scope.steps = $scope.steps.filter(function(step) {
          return step.ready;
        });
      });
    }

    function switchToFirstReadyStep() {
      forEach(steps, function (step, index) {
        /*eslint-disable angular/controller-as */
        if ($scope.currentIndex < 0 && step.ready) {
          $scope.currentIndex = index;
          return;
        }
        /*eslint-enable angular/controller-as */
      });
    }
  }
})();
