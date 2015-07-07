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

/*eslint-disable max-len */
  /**
   * @ngdoc overview
   * @name horizon.framework.widgets.wizard
   * @description
   *
   * # horizon.framework.widgets.wizard
   *
   * The `horizon.framework.widgets.wizard` module provides support for
   * creating a multi-step process to accomplish a task.
   *
   * Requires {@link horizon.framework.widgets.wizard.directive:wizard `wizard`} module to
   * be installed.
   *
   * | Directives                                                               |
   * |--------------------------------------------------------------------------|
   * | {@link horizon.framework.widgets.wizard.directive:wizard `wizard`} |
   *
   * | Controllers                                                               |
   * |---------------------------------------------------------------------------|
   * | {@link horizon.framework.widgets.wizard.controller:WizardController `WizardController`} |
   * | {@link horizon.framework.widgets.wizard.controller:ModalContainerController 'ModalContainerController'} |
   */
/*eslint-enable max-len */
  angular
    .module('horizon.framework.widgets.wizard', [])

    .constant('horizon.framework.widgets.wizard.labels', {
      cancel: gettext('Cancel'),
      back: gettext('Back'),
      next: gettext('Next'),
      finish: gettext('Finish')
    })

    .constant('horizon.framework.widgets.wizard.events', {
      ON_INIT_SUCCESS: 'ON_INIT_SUCCESS',
      ON_INIT_ERROR: 'ON_INIT_ERROR',
      ON_SWITCH: 'ON_SWITCH',
      BEFORE_SUBMIT: 'BEFORE_SUBMIT',
      AFTER_SUBMIT: 'AFTER_SUBMIT'
    });
})();
