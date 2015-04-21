/*
 * Copyright 2015 IBM Corp.
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 * http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */
(function() {
  'use_strict';

  /**
   * @ngdoc overview
   * @name hz.widget.toast
   * description
   *
   * # hz.widget.toast
   *
   * The `hz.widget.toast` module provides pop-up notifications to Horizon.
   * A toast is a short text message triggered by a user action to provide
   * real-time information. Toasts do not disrupt the page's behavior and
   * typically auto-expire and fade. Also, toasts do not accept any user
   * interaction.
   *
   *
   * | Components                                                               |
   * |--------------------------------------------------------------------------|
   * | {@link hz.widget.toast.factory:toastService `toastService`}              |
   * | {@link hz.widget.toast.directive:toast `toast`}                          |
   *
   */
  angular.module('hz.widget.toast', [])

    /**
     * @ngdoc service
     * @name toastService
     *
     * @description
     * This service can be used to display user messages, toasts, in Horizon.
     * To create a new toast, inject the 'toastService' module into your
     * current module. Then, use the service methods.
     *
     * For example to add a 'success' message:
     *     toastService.add('success', 'User successfully created.');
     *
     * All actions (add, clearAll, etc.) taken on the data are automatically
     * sync-ed with the HTML.
     */
    .factory('toastService', function() {

      var toasts = [];
      var service = {};

      /**
       * Helper method used to remove all the toasts matching the 'type'
       * passed in.
       */
      function clear(type) {
        for (var i = toasts.length - 1; i >= 0; i--) {
          if (toasts[i].type === type) {
            toasts.splice(i, 1);
          }
        }
      }

      /**
       * There are 5 types of toasts, which are based off Bootstrap alerts.
       */
      service.types = {
        danger: gettext('Danger'),
        warning: gettext('Warning'),
        info: gettext('Info'),
        success: gettext('Success'),
        error: gettext('Error')
      };

      /**
       * Create a toast object and push it to the toasts array.
       */
      service.add = function(type, msg) {
        var toast = {
          type: type === 'error' ? 'danger' : type,
          typeMsg: this.types[type],
          msg: msg,
          close: function(index) {
            toasts.splice(index, 1);
          }
        };
        toasts.push(toast);
      };

      /**
       * Remove a single toast.
       */
      service.close = function(index) {
        toasts.splice(index, 1);
      };

      /**
       * Return all toasts.
       */
      service.get = function() {
        return toasts;
      };

      /**
       * Remove all toasts.
       */
      service.clearAll = function() {
        toasts = [];
      };

      /**
       * Remove all toasts of type 'danger.'
       */
      service.clearErrors = function() {
        clear('danger');
      };

      /**
       * Remove all toasts of type 'success.'
       */
      service.clearSuccesses = function() {
        clear('success');
      };

      return service;

    })

    /**
     * @ngdoc directive
     * @name hz.widget.toast.directive:toast
     *
     * @description
     * The `toast` directive allows you to place the toasts wherever you
     * want in your layout. Currently styling is pulled from Bootstrap alerts.
     *
     * @restrict EA
     * @scope true
     *
     */
    .directive('toast', ['toastService', 'basePath', function(toastService, path) {
      return {
        restrict: 'EA',
        templateUrl: path + 'toast/toast.html',
        scope: {},
        link: function(scope) {
          scope.toast = toastService;
        }
      };
    }]);

})();
