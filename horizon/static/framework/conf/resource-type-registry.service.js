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

  angular.module('horizon.framework.conf')

  .factory('horizon.framework.conf.resource-type-registry.service', registryService);

  registryService.$inject = [
    'horizon.framework.util.extensible.service'
  ];

  /*
   * @ngdoc service
   * @name horizon.framework.conf.resource-type-registry.service
   * @description
   * This service provides a registry which allows for registration of
   * configurations for resource types.  These configurations include
   * batch and item actions, which are associated with the resource type
   * via a key.  The key follows the format: OS::Glance::Image.
   * The functions that are exposed both assist with registration and also
   * provide utilities relevant for their consumption.
   * This service uses the extensibility service to decorate the individual
   * containers for the actions, so they may be best manipulated via its
   * decorated methods.
   * The concept for use is to register actions with the resource types at
   * the Angular module level, using the .run() function.  This allows
   * actions to be configured by any module.
   * Actions should not perform complex actions in their construction, for
   * example API calls, because as injectables their constructor is run
   * during injection, meaning API calls would be executed as the module
   * is initialized.  This would mean those calls would be executed on any
   * Angular context initialization, such as going to the login page.  Actions
   * should instead place such code in their initScope() functions.
   */
  function registryService(extensibleService) {

    /*
     * @ngdoc function
     * @name getMember
     * @description
     * Given a resource type name and the member type (e.g. 'itemActions')
     * This returns the extensible container for those inputs.  If either
     * requested item hasn't been initialized yet, they are created.
     */
    function getMember(type, member) {
      if (!resourceTypes.hasOwnProperty(type)) {
        resourceTypes[type] = {};
      }
      if (!resourceTypes[type].hasOwnProperty(member)) {
        resourceTypes[type][member] = [];
        extensibleService(resourceTypes[type][member],
          resourceTypes[type][member]);
      }

      return resourceTypes[type][member];
    }

    /*
     * @ngdoc function
     * @name getMemberFunction
     * @description
     * Returns a function that returns the requested items.  This is only
     * present as a utility function for the benefit of the action directive.
     */
    function getMemberFunction(type, member) {
      return function() { return resourceTypes[type][member]; };
    }

    var resourceTypes = {};
    var registry = {
      getItemActions: getItemActions,
      getItemActionsFunction: getItemActionsFunction,
      initActions: initActions,
      getBatchActions: getBatchActions,
      getBatchActionsFunction: getBatchActionsFunction
    };

    /*
     * @ngdoc function
     * @name getItemActions
     * @description
     * Retrieves the type's item actions.
     */
    function getItemActions(type) {
      return getMember(type, 'itemActions');
    }

    /*
     * @ngdoc function
     * @name getItemActionsFunction
     * @description
     * Retrieves a function returning the type's item actions.
     */
    function getItemActionsFunction(type) {
      return getMemberFunction(type, 'itemActions');
    }

    /*
     * @ngdoc function
     * @name initActions
     * @description
     * Performs initialization (namely, scope-setting) of all actions
     * for the given type.  This requires the proper scope be passed.
     * If an action does not have an initScope() function, it is ignored.
     */
    function initActions(type, scope) {
      angular.forEach(resourceTypes[type].itemActions, setActionScope);
      angular.forEach(resourceTypes[type].batchActions, setActionScope);

      function setActionScope(action) {
        if (action.service.initScope) {
          action.service.initScope(scope.$new());
        }
      }
    }

    /*
     * @ngdoc function
     * @name getBatchActions
     * @description
     * Retrieves the type's batch actions.
     */
    function getBatchActions(type) {
      return getMember(type, 'batchActions');
    }

    /*
     * @ngdoc function
     * @name getBatchActionsFunction
     * @description
     * Retrieves a function returning the type's batch actions.
     */
    function getBatchActionsFunction(type) {
      return getMemberFunction(type, 'batchActions');
    }

    return registry;
  }

})();
