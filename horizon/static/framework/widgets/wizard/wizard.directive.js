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

  angular
    .module('horizon.framework.widgets.wizard')
    .directive('wizard', wizard);

  wizard.$inject = ['horizon.framework.widgets.basePath'];

  /**
    * @ngdoc directive
    * @name horizon.framework.widgets.wizard.directive:wizard
    * @description
    * The `wizard` directive allows you to create a multi-step process to accomplish a task.
    * Inside the wizard, you can have as many steps as you want. Each step acts like a form;
    * and the submit button will only show when all the steps are complete and valid.
    */
  function wizard(basePath) {
    var directive = {
      controller: 'WizardController',
      templateUrl: basePath + 'wizard/wizard.html'
    };
    return directive;
  }
})();
