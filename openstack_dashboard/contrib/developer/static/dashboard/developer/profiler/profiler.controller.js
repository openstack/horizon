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
    .controller('topProfilerController', topProfilerController)
    .controller('sharedProfilerController', sharedProfilerController)
    .controller('profilerActionsController', actionsController);

  /**
   * @ngdoc controller
   * @name horizon.dashboard.developer.topProfilerController
   * @description
   * This is the top-level controller for the Profiler view.
   * Its primary purpose is hand the list of traces over to profiler table widget.
   */
  topProfilerController.$inject = ['horizon.framework.util.http.service'];
  function topProfilerController($http) {
    var ctrl = this;

    $http.get('/api/profiler/traces').then(function(response) {
      ctrl.traces = response.data;
      ctrl.tracesDisplayed = response.data;
    });

  }

  /**
   * @ngdoc controller
   * @name horizon.dashboard.developer.sharedProfilerController
   * @description
   * This is the controller being used inside <trace-table> directive, it is
   * shared between all the trace node directives which recursively form the
   * whole trace (hence the name). It contains various helper methods which
   * are used while rendering trace node.
   */
  sharedProfilerController.$inject = [
    '$uibModal',
    '$rootScope',
    '$templateCache',
    'horizon.dashboard.developer.profiler.basePath'
  ];
  function sharedProfilerController($modal, $rootScope, $templateCache, basePath) {
    var ctrl = this;
    ctrl.getWidth = getWidth;
    ctrl.getStarted = getStarted;
    ctrl.isImportant = isImportant;
    ctrl.display = display;
    ctrl.toggleChildren = toggleChildren;
    ctrl.getLeafCls = getLeafCls;
    ctrl.getBranchCls = getBranchCls;

    function toggleChildren(data) {
      function rec(data, value, nonRoot) {
        if (nonRoot) {
          data.visible = value;
        }
        // don't expand nodes collapsed explicitly when expanding one of their
        // parents
        if (!(value && !data.childrenVisible)) {
          data.children.forEach(function(child) {
            rec(child, value, true);
          });
        }
      }
      data.childrenVisible = !data.childrenVisible;
      rec(data, data.childrenVisible);
    }

    function getLeafCls(data) {
      return data.is_leaf ? 'fa-cloud' : '';
    }

    function getBranchCls(data) {
      if (!data.children.length) {
        return '';
      }
      return data.children[0].visible ? 'fa-minus' : 'fa-plus';
    }

    function getWidth(data, rootData) {
      var full_duration = rootData.info.max_finished;
      var duration = (data.info.finished - data.info.started) * 100.0 / full_duration;
      return (duration >= 0.5) ? duration : 0.5;
    }

    function getStarted(data, rootData) {
      var full_duration = rootData.info.max_finished;
      return data.info.started * 100.0 / full_duration;
    }

    function isImportant(data) {
      return ["total", "wsgi", "rpc"].indexOf(data.info.name) != -1;
    }

    function display(data){
      var scope = $rootScope.$new();
      var info = angular.copy(data.info);
      var metadata = {};
      angular.forEach(info, function(value, key) {
        var parts = key.split(".");
        if (parts[0] == "meta") {
          if (parts.length == 2){
            this[parts[1]] = value;
          }
          else{
            var group_name = parts[1];
            if (!(group_name in this))
              this[group_name] = {};
            this[group_name][parts[2]] = value;
          }
        }
      }, metadata);
      info["duration"] = info["finished"] - info["started"];
      info["metadata"] = JSON.stringify(metadata, "", 4);
      scope.info = info;
      scope.columns = ["name", "project", "service", "host", "started",
        "finished", "duration", "metadata"];
      $modal.open({
        "size": "lg",
        "template": $templateCache.get(basePath + 'profiler.details.html'),
        "scope": scope
      });
    }
  }

  /**
   * @ngdoc controller
   * @name horizon.dashboard.developer.profilerActionsController
   * @description
   * This is the controller being used in header partial template for invoking
   * various profiling actions through a drop-down control.
   */
  actionsController.$inject = ['$cookies'];
  function actionsController($cookies) {
    var ctrl = this;

    ctrl.profilePage = profilePage;

    function profilePage() {
      $cookies.put('profile_page', true, {path: window.location.pathname});
      window.location.reload();
    }
  }
})();
