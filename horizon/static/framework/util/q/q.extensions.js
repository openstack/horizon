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
(function() {
  'use strict';

  angular
    .module('horizon.framework.util.q')
    .factory('horizon.framework.util.q.extensions', qExtensions);

  qExtensions.$inject = ['$q'];

  /**
   * @ngdoc factory
   * @name horizon.framework.util.q:extensions
   * @module horizon.framework.util.q
   * @kind function
   * @description
   *
   * Extends the $q from Angular to provide additional functionality.
   *
   */
  function qExtensions($q) {
    var service = {
      allSettled: allSettled,
      booleanAsPromise: booleanAsPromise
    };

    return service;

    /**
     * Allow all given promises to settle and returns a collection
     * of the successful and failed responses allowing the caller
     * to make decisions based on the individual results.
     *
     * This function is typically used if you need all promises
     * to complete and get all of the success and response messages,
     * but need to correlate specific success and failure results
     * to a particular context. To do this, ensure that the passed
     * in promise has a context attribute available on the input
     * promise. Each result or failure reason will include the
     * context in the fail or pass array.
     *
     * It will always result in a success callback (resolved),
     * but will provide a summary object of the results in a pair
     * of arrays ("pass" and "fail"), even if some of the promises fail.
     * The "pass" array will contain each of the results of the
     * successfully resolved promises and the "fail" array
     * will return each of the reasons for the rejected promises.
     *
     * In contrast to the `$q.all` in Angular which will terminate all
     * promises if any promise is rejected, this will wait for all promises
     * to settle.
     *
     * The order of the resolve or rejection reasons correlates directly to
     * the order of the promises in the list.
     *
     * @param {array} promiseList
     * The list of promises to resolve
     *
     * @return {object}
     * An object with 2 lists, one for promises that got resolved
     * and one for promises that got rejected.
     *
     * @example
     * ```
     * var settledPromises = qExtenstions.allSettled([
     *   {promise: promise1, context: context1},
     *   {promise: promise2, context: context2}
     * ]);
     * settledPromises.then(onSettled);
     *
     * function onSettled(data) {
     *   doSomething(data.pass);
     *   doSomething(data.fail);
     * }
     *
     * function doSomething(resolvedList) {
     *   resolvedList.forEach(function (item) {
     *     console.log("context", item.context, "result", item.data);
     *   });
     * }
     */
    function allSettled(promiseList) {
      var deferred = $q.defer();
      var passList = [];
      var failList = [];
      var promises = promiseList.map(resolveSingle);

      $q.all(promises).then(onComplete);
      return deferred.promise;

      function resolveSingle(singlePromise, index) {
        var deferredInner = $q.defer();
        singlePromise.promise.then(onResolve, onReject);
        return deferredInner.promise;

        function onResolve(response) {
          passList[index] = formatResponse(response, singlePromise.context);
          deferredInner.resolve();
        }

        function onReject(response) {
          failList[index] = formatResponse(response, singlePromise.context);
          deferredInner.resolve();
        }

        function formatResponse(response, context) {
          return {
            data: response,
            context: context
          };
        }
      }

      function onComplete() {
        deferred.resolve({pass: condense(passList), fail: condense(failList)});
      }

      function condense(promiseList) {
        return promiseList.filter(function removeEmpty(promise) {
          return !!promise;
        });
      }
    }

    /**
     * Create a promise that resolves if true, otherwise is rejected.
     *
     * @param {expression} value
     * the boolean value to test
     *
     * @return {promise}
     * the promise object
     */
    function booleanAsPromise(value) {
      var deferred = $q.defer();

      if (value === true) {
        deferred.resolve();
      } else {
        deferred.reject();
      }

      return deferred.promise;
    }

  }
})();
