/*
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

  /**
   * @ngdoc overview
   * @name horizon.framework.widgets.metadata-display
   * @description
   *
   * # horizon.framework.widgets.metadata-display
   *
   * The `horizon.framework.widgets.metadata-display` provides widget displaying metadata.
   *
   * | Directives                                                                                  |
   * |---------------------------------------------------------------------------------------------|
   * | {@link horizon.framework.widgets.metadata-display.directive:hzMetadataDisplay `hzMetadataDisplay`}          |
   * |---------------------------------------------------------------------------------------------|
   * | Controllers                                                                                 |
   * |---------------------------------------------------------------------------------------------|
   * | {@link horizon.framework.widgets.metadata-display.controller:HzMetadataDisplayController `HzMetadataDisplayController`} |
   *
   */
  angular
    .module('horizon.framework.widgets.metadata-display', [
      'horizon.framework.widgets.metadata-tree'
    ])

  /**
   * @ngdoc parameters
   * @name horizon.framework.widgets.metadata-display:metadataTreeDefaults
   * @param {object} text Text constants
   */
  .constant('horizon.framework.widgets.metadata-display.defaults', {
    text: {
      detail: gettext('Detail Information')
    }
  });
})();
