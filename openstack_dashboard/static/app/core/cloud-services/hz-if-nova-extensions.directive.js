/*
 * (c) Copyright 2015 Hewlett-Packard Development Company, L.P.
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
    .module('horizon.app.core.cloud-services')
    .directive('hzIfNovaExtensions', hzNovaExtensions);

  hzNovaExtensions.$inject =  [
    'hzPromiseToggleTemplateDirective',
    'horizon.app.core.openstack-service-api.novaExtensions'
  ];

  /**
   * @ngdoc directive
   * @name hz.api:directive:hzIfNovaExtensions
   * @module hz.api
   * @description
   *
   * Add this directive to any element containing content which should
   * only be evaluated when the specified nova extensions are enabled by
   * the nova servers in the currently selected region. If the nova extensions
   * are enabled, the content will be evaluated. Otherwise, the content will
   * not be compiled. In addition, the element and everything contained by
   * it will be removed completely, leaving a simple HTML comment.
   *
   * This is evaluated once per page load. In current horizon, this means
   * it will get re-evaluated with events like the user opening another panel,
   * changing logins, or changing their region.
   *
   * The hz-if-nova-extensions attribute may be set to a single extension (String)
   * or an array of extensions (each one being a String).
   * All of the following are examples:
   *
   * hz-if-nova-extensions='"ConfigDrive"'
   * hz-if-nova-extensions='["ConfigDrive"]'
   * hz-if-nova-extensions='["ConfigDrive", "DiskConfig"]'
   *
   * @example
   *
   * In the below, if the ConfigDrive nova extension is not enabled, then
   * the div element with hz-if-nova-extensions and all of the elements inside
   * of it will be removed and never evaluated by the angular compiler.
   *
   ```html
    <div hz-if-nova-extensions='"ConfigDrive"'>
      <!-- ui code here -->
    </div>
   ```
   */
  function hzNovaExtensions(hzPromiseToggleTemplateDirective, novaExtensions) {
    return angular.extend(
        hzPromiseToggleTemplateDirective[0],
        {
          singlePromiseResolver: novaExtensions.ifNameEnabled,
          name: 'hzIfNovaExtensions'
        }
    );
  }

})();
