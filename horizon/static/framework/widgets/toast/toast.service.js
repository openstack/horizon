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
  'use strict';

  /**
    * @ngdoc service
    * @name toastService
    *
    * @description
    * This service can be used to display user messages, toasts, in Horizon.
    * To create a new toast, inject the 'horizon.framework.widgets.toast.service'
    * module into your current module. Then, use the service methods.
    *
    * For example to add a 'success' message:
    *     toastService.add('success', 'User successfully created.');
    *
    * All actions (add, clearAll, etc.) taken on the data are automatically
    * sync-ed with the HTML.
    */
  angular
    .module('horizon.framework.widgets.toast')
    .factory('horizon.framework.widgets.toast.service', toastService);

  toastService.$inject = ['$timeout',
                          'horizon.framework.conf.toastOptions'];

  function toastService($timeout, toastOptions) {

    var toasts = [];
    var service = {
      types: {},
      add: add,
      get: get,
      find: find,
      cancel: cancel,
      clearAll: clearAll,
      clearErrors: clearErrors,
      clearSuccesses: clearSuccesses
    };

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

    return service;

    ///////////////////////

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

    function autoDismiss(toast) {
      $timeout(function dismiss() {
        var index = toasts.indexOf(toast);
        var dismissible = toastOptions.dimissible.indexOf('alert-' + toast.type);
        // check if the toast exists and if it is dismissible (by checking
        // the toastOptions config), then we remove it after a delay
        if (index > -1 && dismissible > -1) {
          toasts.splice(index, 1);
        }
      }, toastOptions.delay);
    }

    /**
     * Remove a single toast.
     */
    function cancel(index) {
      toasts.splice(index, 1);
    }

    /**
      * Create a toast object and push it to the toasts array.
      */
    function add(type, msg) {
      var toast = {
        type: type === 'error' ? 'danger' : type,
        typeMsg: this.types[type],
        msg: msg,
        cancel: cancel
      };
      autoDismiss(toast);
      toasts.push(toast);
    }

    /**
     * Return all toasts.
     */
    function get() {
      return toasts;
    }

    /**
     * find a matching existing toast based on type and message
     *
     * @param type type of the message
     * @param msg  localized message of the toast
     * @returns {*} return toast object if find matching one
     */
    function find(type, msg) {
      return toasts.find(function(toast) {
        var toastType = (type === 'error' ? 'danger' : type);
        return (toast.type === toastType && toast.msg.localeCompare(msg) === 0);
      });
    }

    /**
     * Remove all toasts.
     */
    function clearAll() {
      toasts = [];
    }

    /**
     * Remove all toasts of type 'danger.'
     */
    function clearErrors() {
      clear('danger');
    }

    /**
     * Remove all toasts of type 'success.'
     */
    function clearSuccesses() {
      clear('success');
    }
  }
})();
