/**
 * Copyright 2016, Mirantis, Inc.
 *
 * Licensed under the Apache License, Version 2.0 (the "License"); you may
 * not use this file except in compliance with the License. You may obtain
 * a copy of the License at
 *
 *    http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
 * WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
 * License for the specific language governing permissions and limitations
 * under the License.
 */

(function() {
  'use strict';

  angular
    .module('horizon.framework.widgets.transfer-table')
    .filter('filterAvailable', filterAvailable);

  filterAvailable.$inject = ['horizon.framework.util.filters.$memoize'];
  /**
   * @ngdoc filter
   * @name filterAvailable
   *
   * @param {array} available
   * List of objects being filtered.
   *
   * @param {object} allocatedKeys
   * Dictionary with object keys that should be excluded from filtered output.
   *
   * @param {string} primaryKey (Optional)
   * Attribute name to use as primary key, defaults to 'id'.
   *
   * @returns {array}
   * Filtered list of objects whose keys are NOT present in the dictionary.
   *
   * @description
   *
   * The filter works nicely when used inside ng-repeat directive and does not
   * lead to an infinite digest loop error, thanks to memoizing its results on
   * both the initial list, keys dictionary and key name. For more details see
   * http://stackoverflow.com/a/24213626/4414610
   * Since the filter cache is shared between filter invocations in different
   * contexts, one must namespace entities key values. Consider the following
   * example: there are, two security groups with keys 'test1' and 'test2' and
   * two key pairs with same keys, the combined key for both datasets will be
   * the same. Consequently we will get key pairs in a filter output while
   * expecting security groups, or vice versa. To avoid subtle bugs like that
   * entity keys must be namespaced; a good id of a key pair from Launch Instance
   * wizard transfer table would be 'li_keypair:<keypair_name>'.
   *
   * @example
   *
   * var available = [{
   *   id: 1,
   *   attr: 'one'
   * }, {
   *   id: 2,
   *   attr: 'two'
   * }, {
   *   id: 3,
   *   attr: 'three'
   * }]
   *
   * console.log(filterAvailable(available, [1]))
   * console.log(filterAvailable(available, ['one'], 'attr')) // same result as above
   *
   */
  function filterAvailable($memoize) {
    return $memoize($filterAvailable, $hasher);

    function $idKeyOrDefault(primaryKey) {
      return primaryKey || 'id';
    }

    function arrayIsEmpty(array) {
      return angular.isUndefined(array) || !array.length;
    }

    function emptyObj(obj) {
      return angular.isUndefined(obj) || !Object.keys(obj).length;
    }

    function $hasher(available, allocatedIds, primaryKey) {
      if (arrayIsEmpty(available)) {
        return '';
      }
      primaryKey = $idKeyOrDefault(primaryKey);
      var key = available.map(function(item) {
        return item[primaryKey];
      }).sort().join('_');
      return key + '_' + Object.keys(allocatedIds).sort().join('_');
    }

    function $filterAvailable(available, allocatedKeys, primaryKey) {
      if (arrayIsEmpty(available)) {
        return [];
      } else if (emptyObj(allocatedKeys)) {
        return available;
      }
      primaryKey = $idKeyOrDefault(primaryKey);
      return available.filter(function isItemAvailable(item) {
        return !(item[primaryKey] in allocatedKeys);
      });
    }
  }

})();
