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
    .module("horizon.framework.widgets.headers")
    .directive('hzPageHeader', hzPageHeader);

  hzPageHeader.$inject = ['horizon.framework.widgets.headers.basePath'];

  /**
   * @ngdoc directive
   * @name hzPageHeader
   * @description
   * Provides markup for a general page header.  It takes a title
   * and description and transcludes any given markup.
   *
   * @example
   *
   * Default usage to provide a title header and a description that are
   * translated by the angular gettext translate filter.:
   *
   * <hz-page-header header="{$ 'My Header' | translate $}" description="{$ 'foo' | translate $}"/>
   *
   * If you have additional content that you want to include beneath the
   * title header and description, then include that content inside the
   * directives. Example:
   *
   * <hz-page-header header="{$ 'My Header' | translate $}" description="{$ 'foo' | translate $}">
   *   <a href="http://www.openstack.org">Go to OpenStack</a>
   * </hz-page-header>
   */
  function hzPageHeader(basePath) {
    var directive = {
      restrict: 'E',
      scope: {
        header: '@',
        description: '@'
      },
      templateUrl: basePath + 'hz-page-header.html',
      transclude: true
    };

    return directive;
  }

})();

