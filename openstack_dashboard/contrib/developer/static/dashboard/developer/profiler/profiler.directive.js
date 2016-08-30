/*
 *    (c) Copyright 2015 Mirantis Inc.
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
    .module('horizon.dashboard.developer.profiler')
    .directive('traceTable', traceTable)
    .directive('nodeData', nodeData);

  nodeData.$inject = [
    '$compile',
    '$templateCache',
    'horizon.dashboard.developer.profiler.basePath'];

  function nodeData($compile, $templateCache, basePath) {
    return {
      restrict: 'A',
      scope: {
        hideChildren: '=',
        rootData: '=',
        data: '=nodeData',
        visible: '='
      },
      require: '^traceTable',
      link: function(scope, element, attrs, sharedCtrl) {
        var destroyWatcher = scope.$watch('rootData', function(newValue) {
          if (angular.isDefined(newValue)) {
            var template = $templateCache.get(basePath + 'profiler.tree-node.html');
            scope.ctrl = sharedCtrl;
            element.replaceWith($compile(template)(scope));
          }
        });
        scope.$on('$destroy', function() {
          destroyWatcher();
        });
      }
    }
  }

  traceTable.$inject = [
    'horizon.framework.util.http.service',
    'horizon.dashboard.developer.basePath'];

  function traceTable($http, basePath) {
    return {
      restrict: 'A',
      templateUrl: basePath + 'profiler/profiler.trace-table.html',
      scope: {
        trace: '=traceTable'
      },
      replace: true,
      controller: 'sharedProfilerController',
      link: function(scope) {
        var destroyWatcher = scope.$watch('trace', function(trace) {
          if (trace) {
            var traceId = trace.id;
            scope.$on('hzTable:rowExpanded', function(e, traceItem) {
              if (traceId === traceItem.id && !scope.data) {
                $http.get('/api/profiler/traces/' + traceId).then(function(response) {
                  scope.data = response.data;
                });
              }
            });
          }
        });
        scope.$on('$destroy', function() {
          destroyWatcher();
        });
      }
    }
  }
})();