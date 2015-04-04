(function () {
  'use strict';

  var extend = angular.extend,
      forEach = angular.forEach,
      noop = angular.noop;

  angular.module('hz.widget.wizard', ['ui.bootstrap'])

    .constant('wizardLabels', {
      cancel: gettext('Cancel'),
      back: gettext('Back'),
      next: gettext('Next'),
      finish: gettext('Finish')
    })

    .constant('wizardEvents', {
      ON_INIT_SUCCESS: 'ON_INIT_SUCCESS',
      ON_INIT_ERROR: 'ON_INIT_ERROR',
      ON_SWITCH: 'ON_SWITCH',
      BEFORE_SUBMIT: 'BEFORE_SUBMIT',
      AFTER_SUBMIT: 'AFTER_SUBMIT'
    })

    .directive('wizard', ['basePath', function (path) {
      return {
        controller: ['$scope', '$q', 'wizardLabels', 'wizardEvents',
          function ($scope, $q, wizardLabels, wizardEvents) {
            $scope.currentIndex = -1;
            $scope.openHelp = false;
            $scope.workflow = $scope.workflow || {};
            $scope.btnText = extend({}, wizardLabels, $scope.workflow.btnText);
            $scope.btnIcon = $scope.workflow.btnIcon || {};
            $scope.steps = $scope.workflow.steps || [];
            $scope.wizardForm = {};
            $scope.initTask = $q.defer();
            $scope.initPromise = $scope.initTask.promise;
            $scope.showSpinner = false;
            $scope.hasError = false;

            $scope.switchTo = function (index) {
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
              $scope.currentIndex = index;
              $scope.openHelp = false;
            };
            $scope.showError = function (errorMessage) {
              $scope.showSpinner = false;
              $scope.errorMessage = errorMessage;
              $scope.hasError = true;
            };
            $scope.beforeSubmit = function () {
              $scope.$broadcast(wizardEvents.BEFORE_SUBMIT);
            };
            $scope.afterSubmit = function () {
              $scope.$broadcast(wizardEvents.AFTER_SUBMIT);
              $scope.close();
            };
            $scope.onClickFinishBtn = function () {
              $scope.beforeSubmit();
              $scope.submit().then($scope.afterSubmit, $scope.showError);
            };
            $scope.initPromise.then(
              function () {
                $scope.$broadcast(wizardEvents.ON_INIT_SUCCESS);
              },
              function () {
                $scope.$broadcast(wizardEvents.ON_INIT_ERROR);
              }
            );

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

                      checkReadiness: function () {
                        var d = $q.defer();
                        setTimeout(function () {
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

              forEach($scope.steps, function (step, index) {
                step.ready = !step.checkReadiness;

                if (step.checkReadiness) {
                  var promise = step.checkReadiness();
                  stepReadyPromises.push(promise);
                  promise.then(
                    function () {
                      step.ready = true;
                    },
                    function () {
                      $scope.steps.splice(index, 1);
                    }
                  );
                }
              });

              $scope.ready = (stepReadyPromises.length === 0);
              return $q.all(stepReadyPromises);
            }

            function switchToFirstReadyStep() {
              forEach($scope.steps, function (step, index) {
                if ($scope.currentIndex < 0 && step.ready) {
                  $scope.currentIndex = index;
                  return;
                }
              });
            }

            // angular promise doesn't have #always method right now,
            // this is a simple workaround.
            function always() {
              $scope.ready = true;
              $scope.initTask.resolve();
              switchToFirstReadyStep();
            }

            checkAllReadiness().then(always, always);
          }],
          templateUrl: path + 'wizard/wizard.html'
        };
      }
    ])

    .controller('ModalContainerCtrl', ['$scope', '$modalInstance', 'launchContext',
      function ($scope, $modalInstance, launchContext) {
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
