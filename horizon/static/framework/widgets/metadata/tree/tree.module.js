/*
 * Copyright 2015, Intel Corp.
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

  /*eslint-disable max-len */
  /**
   * @ngdoc overview
   * @name horizon.framework.widgets.metadata.tree
   * @description
   *
   * # horizon.framework.widgets.metadata.tree
   *
   * The `horizon.framework.widgets.metadata.tree` provides widgets and service
   * with logic for editing metadata.
   *
   * | Components                                                                                 |
   * |--------------------------------------------------------------------------------------------|
   * | {@link horizon.framework.widgets.metadata.tree.directive:metadataTree `metadataTree`}      |
   * | {@link horizon.framework.widgets.metadata.tree.directive:metadataTreeItem `metadataTreeItem`} |
   * | {@link horizon.framework.widgets.metadata.tree.directive:metadataTreeUnique `metadataTreeUnique`} |
   * | {@link horizon.framework.widgets.metadata.tree.controller:MetadataTreeController `MetadataTreeController`} |
   * | {@link horizon.framework.widgets.metadata.tree.controller:MetadataTreeItemController `MetadataTreeItemController`} |
   *
   */
  /*eslint-enable max-len */
  angular
    .module('horizon.framework.widgets.metadata.tree', [], config)
    .constant('horizon.framework.widgets.metadata.tree.defaults', {
      text: {
        /*eslint-disable max-len */
        help: gettext('You can specify resource metadata by moving items from the left column to the right column. In the left column there are metadata definitions from the Glance Metadata Catalog. Use the "Custom" option to add metadata with the key of your choice.'),
        /*eslint-enable max-len */
        min: gettext('Min'),
        max: gettext('Max'),
        minLength: gettext('Min length'),
        maxLength: gettext('Max length'),
        patternMismatch: gettext('Pattern mismatch'),
        integerRequired: gettext('Integer required'),
        decimalRequired: gettext('Decimal required'),
        required: gettext('Required'),
        duplicate: gettext('Duplicate keys are not allowed'),
        filter: gettext('Filter'),
        available: gettext('Available Metadata'),
        existing: gettext('Existing Metadata'),
        custom: gettext('Custom'),
        noAvailable: gettext('No available metadata'),
        noExisting: gettext('No existing metadata')
      }
    });

  config.$inject = ['$provide', '$windowProvider'];

  function config($provide, $windowProvider) {
    var path = $windowProvider.$get().STATIC_URL + 'framework/widgets/metadata/tree/';
    $provide.constant('horizon.framework.widgets.metadata.tree.basePath', path);
  }

})();
