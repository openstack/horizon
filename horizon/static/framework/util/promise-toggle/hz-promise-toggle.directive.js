/**
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
    .module('horizon.framework.util.promise-toggle')
    .directive('hzPromiseToggleTemplate', hzPromiseToggleTemplate);

  /**
   * @ngdoc directive
   * @name horizon.framework.util.promise-toggle:directive:hzPromiseToggleTemplate
   * @module horizon.framework.util.promise-toggle
   * @description
   *
   * A template directive that can be used for creating additional directives
   * which will only compile their transcluded content if all of the promises
   * associated with the directive resolve.
   *
   * This supports declarative directives that compile in their
   * content only after the related promises resolve. This is typically
   * intended to be used for very fast checks (often cached) of whether or
   * not a particular setting or required service is enabled. This should not
   * be used for checks that have frequently changing content, because this
   * is evaluated once per page load.
   *
   * The actual name of whatever directive this is after being extended
   * (angular.extend) should be set to the input that will be passed
   * into the promise resolver. The promise resolver will either resolve
   * or reject the promise. If it resolves, the content inside of the
   * element will be linked in. Otherwise, it will be removed completely.
   * When the input is an array, each element of the array will be treated
   * as a distinct input and a single promise resolver will be invoked for
   * each input element. When that is done, all promises must resolve in
   * order for the content to be linked in. If any of them are rejected,
   * the element will be removed.
   *
   * When extending, the name and singlePromiseResolver must be specified.
   * Other properties may also be overridden for additional customization.
   *
   * @example
   *
   * To use this, simply create a concrete directive using angular.extend:
   *
   *  angular
   *    .module('horizon.framework.util.promise-toggle')
   *    .directive('hzPromiseToggleMock', hzPromiseToggleMock);
   *
   *  hzPromiseToggleMock.$inject =  [
   *    'hzPromiseToggleTemplateDirective',
   *    'mockService'
   *  ];
   *
   *  function hzPromiseToggleMock(hzPromiseToggleTemplateDirective, mockService) {
   *    return angular.extend(
   *        hzPromiseToggleTemplateDirective[0],
   *        {
   *          singlePromiseResolver: mockService.mockResolver,
   *          name: 'hzPromiseToggleMock'
   *        }
   *    );
   *  }
   *
   * Then in the HMTL:
   *
   * <div hz-promize-toggle-mock='["Hello"]'>Your content </div>
   * For single input / single promise resolution:
   *
   * <div hz-promize-toggle-mock='["Hello", "World"]'>Your content </div>
   * For multiple input / multiple promise resolution:
   *
   */

  hzPromiseToggleTemplate.$inject = ['$q', '$parse'];

  function hzPromiseToggleTemplate($q, $parse) {
    var directive = {
      name: null,
      singlePromiseResolver: null,
      transclude: 'element',
      priority: 2000,
      terminal: true,
      restrict: 'A',
      compile: compile,
      $$tlb: true
    };

    return directive;

    ////////////////

    function compile(element, attrs, linker) {
      var input = $parse(attrs[this.name]);
      var singlePromiseResolver = this.singlePromiseResolver;

      return resolvePromises;

      ////////////////

      function resolvePromises(scope, iterStartElement) {
        var resolvedInput = input(scope);

        var promiseResolver = angular.isArray(resolvedInput) ?
            multiPromiseResolver(singlePromiseResolver, resolvedInput) :
            singlePromiseResolver(resolvedInput);

        promiseResolver.then(linkContent, removeContent);

        function linkContent() {
          linker(scope, function (clone) {
            iterStartElement.after(clone);
          });
        }

        function removeContent() {
          element.remove();
        }

        function multiPromiseResolver(resolver, arrayInput) {
          // Resolves each individual input against the promise resolver.
          // If any fail, all will fail.
          return $q.all(
            arrayInput.map(function (singleInput) {
              return resolver(singleInput);
            })
          );
        }
      }
    }
  }

})();
