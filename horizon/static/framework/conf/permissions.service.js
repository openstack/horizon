/*
 * (c) Copyright 2016 Hewlett Packard Enterprise Development LP
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
(function () {
  'use strict';

  angular
    .module('horizon.framework.conf')
    .service('horizon.framework.conf.permissions.service', Permissions);

  Permissions.$inject = ['$q'];

  /**
   * @ngdoc service
   * @name horizon.framework.conf.permissions
   * @module horizon.framework.conf
   *
   * This service provides a common set of a promise based permission checking that
   * can be applied to various entities in horizon. In the most basic case,
   * this code executes the allowed() function (if it exists) on
   * items passed in and returns the promise which will either resolve
   * if the item should be allowed or reject if it should not be allowed.
   * An example of an item passed in might be a hz-dynamic-table column spec.
   * See that code for an example of permissionService in use.
   *
   * Horizon is technically a set of application agnostic widgets and utilities
   * that can be used for various applications. The OpenStack Dashboard is
   * an implementation that uses these widgets. Many of these widgets, such
   * as hz-dynamic-table may need to be displayed based on a variety of permissions
   * that are application specific and that are more simply expressed in a declarative
   * matter rather than functional code such as the allowed function. This service
   * provides this capability by allowing applications to decorate this service and
   * override the extendedPermissions function.
   *
   * In the openstack dashboard additional checks beyond the simple allowed() function
   * are added to this service in the app.core.conf permissionsDecorator,
   * including policies, services and settings.
   */
  function Permissions($q) {
    var service = {
      checkAllowed: checkAllowed,
      checkAll: checkAll,
      extendedPermissions: extendedPermissions
    };

    return service;

    /**
     * If this input configItem has an allowed function, this will execute it and return
     * the promise. Otherwise it will return a resolved promise.
     */
    function checkAllowed(configItem) {
      if (angular.isFunction(configItem.allowed)) {
        return configItem.allowed();
      } else {
        return $q.when(true);
      }
    }

    /**
     * On the given configItem, this will get configItem.allowed and get each
     * additional property matching a permission defined in extended permissions.
     * All of the promises will then be run using $q.all. If all promises resolve
     * then this will resolve. Otherwise, this will reject.
     *
     * When the input to any given permission is an array, each element will be
     * treated as a distinct permission and a single promise resolver will be invoked for
     * each input element.
     *
     * @example
     *
     * In openstack dashboard, each of the policies in the below array will result in a distinct
     * policy check and all of the policies must pass in order for this to permit (resolve) the
     * permissions check.
     *
     *  configItem.policies = [{ rules: [["identity", "identity:get_project"]] }, { <rule 2>}]
     */
    function checkAll(configItem) {
      var promises = [];
      promises = promises.concat(getConfigurationPromises(configItem));
      promises.push(checkAllowed(configItem));
      return $q.all(promises);
    }

    /*
     * This defines all additional permissions that can be defined on the input configItem
     * of checkAll. This is a function that returns an object definition where
     * each property on the object is the name of a permission that can be set on
     * the configItem in order have permission to access / use whatever is being requested.
     * The value of each property should be a promise that can resolve a single instance of that
     * permission. When the input to any given permission is an array, each element will be
     * treated as a distinct input and a single promise resolver will be invoked for
     * each input element.
     *
     * Since this is part of the horizon framework, it defaults to returning an empty object.
     * However, individual applications can decorate this service and override this
     * function to provide common permissions for their application.
     *
     * @example
     *
     * Openstack Dashboard may set permissions for required policies, services, or settings
     * (amongst other items). To do this, the service would be decorated like the following:
     *
       function decorator($delegate, policy, serviceCatalog, settings) {
         var permissionsService = $delegate;

         permissionsService.extendedPermissions = extendedPermissions;

         function extendedPermissions() {
           return {
             policies: policy.ifAllowed,
             services: serviceCatalog.ifTypeEnabled,
             settings: settings.ifEnabled
           };
         }

         return $delegate;
       }
     }
     */
    function extendedPermissions() {
      return {};
    }

    function getConfigurationPromises(configItem) {

      var promises = [];

      angular.forEach(service.extendedPermissions, checkPermissions);

      function checkPermissions(permissionResolver, permissionName) {
        var permissionInput = configItem[permissionName];
        if (angular.isArray(permissionInput)) {
          angular.forEach(permissionInput, function addPermissionCheck(singlePermissionInput) {
            promises.push(permissionResolver(singlePermissionInput));
          });
        } else if (angular.isDefined(permissionInput)) {
          promises.push(permissionResolver(permissionInput));
        }
      }

      return promises;
    }

  }
})();
