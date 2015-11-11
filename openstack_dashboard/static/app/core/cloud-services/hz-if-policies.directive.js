/*
 * Copyright 2015 IBM Corp.
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 * http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

(function () {
  'use strict';

  angular
    .module('horizon.app.core.cloud-services')
    .directive('hzIfPolicies', hzIfPolicies);

  hzIfPolicies.$inject =  [
    'hzPromiseToggleTemplateDirective',
    'horizon.app.core.openstack-service-api.policy'
  ];

  /**
   * @ngdoc directive
   * @name horizon.app.core.cloud-services:hzIfPolicies
   * @module horizon.app.core.cloud-services
   *
   * @description
   * Add this directive to any element containing content which should only be
   * evaluated if the user has permission according to the specified policy rules.
   * If the user has permission, the content will be evaluated. Otherwise,
   * the content will not be compiled.
   *
   * In addition, the element and everything contained by it will
   * be removed completely, leaving a simple HTML comment.
   *
   * This is evaluated once per page load. In current horizon,
   * this means it will get re-evaluated with events like the
   * user opening another panel, changing logins, or changing their region.
   *
   * @example
   * Assume you have the following policy defined in your controller:
   * ctrl.policy = { rules: [["identity", "identity:update_user"]] }
   *
   * Then in your HTML, use it like so:
   ```html
    <div hz-if-policies='ctrl.policy'>
      <span>I am visible if the policy is allowed!</span>
    </div>
   ```
   */
  function hzIfPolicies(hzPromiseToggle, policy) {
    return angular.extend(hzPromiseToggle[0], {
      singlePromiseResolver: policy.ifAllowed,
      name: 'hzIfPolicies'
    });
  }

})();
