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
(function () {
  'use strict';

  angular
    .module('horizon.framework.util.filters')
    .factory('horizon.framework.util.filters.$memoize', $memoize);

  /**
   * @ngdoc factory
   * @name horizon.framework.util.filters.$memoize
   * @module horizon.framework.util.filters
   * @kind function
   * @description
   *
   * Provides a decorator service to memoize results of function calls.
   *
   */
  function $memoize() {
    /**
     * Memoizes a given function by caching the computed result. Useful for
     * speeding up slow-running computations. If passed an optional hashFunction,
     * it will be used to compute the hash key for storing the result, based on
     * the arguments to the original function. The default hashFunction just uses
     * the first argument to the memoized function as the key. The cache of
     * memoized values is available as the cache property on the returned
     * function.
     *
     * @param {function} func
     * The function calls to which are need to be memoized (i.e., cached).
     *
     * @param {function} hasher
     * Function which is used to calculate a key under which the memoized result
     * is stored in cache. Can be omitted for functions that take only a single
     * argument of a scalar type (string, number, boolean). For any function that
     * takes at least one argument of {array} or {object} type, or more than one
     * argument providing this function is crucial. Hasher function should
     * provide unique keys for a set of input arguments which produce unique
     * output.
     *
     * @return {function}
     * The decorated version of function func, which calls are cached.
     *
     * @example
     * ```
     * function getFactorials(numbers) {
     *   if (!angular.isArray(numbers)) {
     *     return 0;
     *   } else {
     *     return numbers.map(function(number) {
     *       var acc = 1;
     *       for (var n = number; n > 0; n--) {
     *         acc *= n;
     *       }
     *       return acc;
     *     }
     *   }
     * }
     *
     * function hasher(numbers) {
     *   return numbers.join(',')
     * }
     *
     * var memoizedGetFactorials = $memoize(getFactorials, hasher);
     */
    return function(func, hasher) {
      var memoize = function(key) {
        var cache = memoize.cache;
        var address = '' + (hasher ? hasher.apply(this, arguments) : key);
        if (!cache.hasOwnProperty(address)) {
          cache[address] = func.apply(this, arguments);
        }
        return cache[address];
      };
      memoize.cache = {};
      return memoize;
    };
  }
}());
