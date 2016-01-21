/**
 * Copyright 2015 IBM Corp
 * (c) Copyright 2015 Hewlett-Packard Development Company, L.P.
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
(function () {
  'use strict';

  angular
    .module('horizon.app.core.openstack-service-api')
    .factory('horizon.app.core.openstack-service-api.settings', settingsService);

  settingsService.$inject = [
    '$q',
    'horizon.framework.util.http.service'
  ];

  /**
   * @ngdoc service
   * @name horizon.app.core.openstack-service-api.settings
   * @description
   * Provides utilities to the cached settings data. This helps
   * with asynchronous data loading.
   *
   * The cache in current horizon (Kilo non-single page app) only has a
   * lifetime of the current page. The cache is reloaded every time you change
   * panels. It also happens when you change the region selector at the top
   * of the page, and when you log back in.
   *
   * So, at least for now, this seems to be a reliable way that will
   * make only a single request to get user information for a
   * particular page or modal. Making this a service allows it to be injected
   * and used transparently where needed without making every single use of it
   * pass it through as an argument.
   */
  function settingsService($q, apiService) {

    var service = {
      getSettings: getSettings,
      getSetting: getSetting,
      ifEnabled: ifEnabled
    };

    return service;

    ///////////////

    /**
     * @name horizon.app.core.openstack-service-api.config.getSettings
     * @description
     * Gets all the allowed settings
     *
     * Returns an object with settings.
     */
    function getSettings(suppressError) {

      function onError() {
        var message = gettext('Unable to retrieve settings.');
        if (!suppressError && horizon.alert) {
          horizon.alert('error', message);
        }

        return message;
      }

      // The below ensures that errors are handled like other
      // service errors (for better or worse), but when successful
      // unwraps the success result data for direct consumption.
      return apiService.get('/api/settings/', {cache: true})
        .error(onError)
        .then(function (response) {
          return response.data;
        });
    }

    /**
     * @name horizon.app.core.openstack-service-api.settings.getSetting
     * @description
     * This retrieves a specific setting.
     *
     * If the setting isn't found, it will return undefined unless a default
     * is specified. In that case, the default will be returned.
     *
     * @param {string} path The path to the setting to get.
     *
     * local_settings.py allows you to create settings such as:
     *
     * OPENSTACK_HYPERVISOR_FEATURES = {
     *    'can_set_mount_point': True,
     *    'can_set_password': False,
     * }
     *
     * To access a specific setting, use a simplified path where a . (dot)
     * separates elements in the path.  So in the above example, the paths
     * would be:
     *
     * OPENSTACK_HYPERVISOR_FEATURES.can_set_mount_point
     * OPENSTACK_HYPERVISOR_FEATURES.can_set_password
     *
     * @param {Object} defaultSetting If the requested setting does not exist,
     * the defaultSetting will be returned. This is optional.
     *
     * @example
     *
     * Using the OPENSTACK_HYPERVISOR_FEATURES mentioned above, the following
     * would call doSomething and pass the setting value into doSomething.
     *
     ```js
        settingsService.getSetting('OPENSTACK_HYPERVISOR_FEATURES.can_set_mount_point')
          .then(doSomething);
     ```
     */
    function getSetting(path, defaultSetting) {
      var deferred = $q.defer();
      var pathElements = path.split(".");
      var settingAtRequestedPath;

      function onSettingsLoaded(settings) {
        // This recursively traverses the object hierarchy until either all the
        // path elements are traversed or until the next element in the path
        // does not have the requested child object.
        settingAtRequestedPath = pathElements.reduce(
          function (setting, nextPathElement) {
            return setting ? setting[nextPathElement] : undefined;//eslint-disable-line no-undefined
          }, settings);

        if (angular.isUndefined(settingAtRequestedPath) && angular.isDefined(defaultSetting)) {
          settingAtRequestedPath = defaultSetting;
        }

        deferred.resolve(settingAtRequestedPath);
      }

      function onSettingsFailure(message) {
        deferred.reject(message);
      }

      service.getSettings()
        .then(onSettingsLoaded, onSettingsFailure);

      return deferred.promise;
    }

    /**
     * @name horizon.app.core.openstack-service-api.settings.ifEnabled
     * @description
     * Checks if the desired setting is enabled. This returns a promise.
     * If the setting is enabled, the promise will be resolved.
     * If it is not enabled, the promise will be rejected. Use it like you
     * would normal promises.
     *
     * @param {string} setting The path to the setting to check.
     * local_settings.py allows you to create settings such as:
     *
     * OPENSTACK_HYPERVISOR_FEATURES = {
     *    'can_set_mount_point': True,
     *    'can_set_password': False,
     * }
     *
     * To access a specific setting, use a simplified path where a . (dot)
     * separates elements in the path.  So in the above example, the paths
     * would be:
     *
     * OPENSTACK_HYPERVISOR_FEATURES.can_set_mount_point
     * OPENSTACK_HYPERVISOR_FEATURES.can_set_password
     *
     * @param {Object} [expected=true] Used to determine if the setting is
     * enabled. The actual setting will be evaluated against the expected
     * value using angular.equals(). If they are equal, then it will be
     * considered enabled. This is optional and defaults to True.
     *
     * @param {Object} [defaultSetting=true] If the requested setting does not exist,
     * the defaultSetting will be used for evaluation. This is optional. If
     * not specified and the setting is not specified, then the setting will
     * not be considered to be enabled.
     *
     * @example
     * Simple true / false example:
     *
     * Using the OPENSTACK_HYPERVISOR_FEATURES mentioned above, the following
     * would call the "setMountPoint" function only if
     * OPENSTACK_HYPERVISOR_FEATURES.can_set_mount_point is set to true.
     *
     ```js
        settingsService.ifEnabled('OPENSTACK_HYPERVISOR_FEATURES.can_set_mount_point')
          .then(setMountPoint);
     ```
     *
     * Evaluating other types of settings:
     *
     * local_settings.py allows you optionally set the enabled OpenStack
     * Service API versions with the following setting:
     *
     *  OPENSTACK_API_VERSIONS = {
     *     "data-processing": 1.1,
     *     "identity": 3,
     *     "volume": 2,
     * }
     *
     * The above is a nested object structure. The simplified path to the
     * volume service version is OPENSTACK_API_VERSIONS.volume
     *
     * It is not uncommon for different OpenStack deployments to have
     * different versions of the service enabled for various reasons.
     *
     * So, now, assume that if version 2 of the volume service (Cinder) is
     * enabled that you want to do something.  If it isn't, then you will do
     * something else.
     *
     * Assume doSomethingIfVersion2 is a function you want to call if version 2
     * is enabled.
     *
     * Assume doSomethingElse is a function that does something else if
     * version 2 is not enabled (optional)
     *
     ```js
        settingsService.ifEnabled('OPENSTACK_API_VERSIONS.volume', 2)
          .then(doSomethingIfVersion2, doSomethingElse);
     ```
     *
     * Now assume that if nothing is set in local_settings, that you want to
     * treat the result as if version 1 is enabled (default when nothing set).
     *
     ```js
        settingsService.ifEnabled('OPENSTACK_API_VERSIONS.volume', 2, 1)
          .then(doSomethingIfVersion2, doSomethingElse);
     ```
     */
    function ifEnabled(setting, expected, defaultSetting) {
      var deferred = $q.defer();

      // If expected is not defined, we default to expecting the setting
      // to be 'true' in order for it to be considered enabled.
      expected = angular.isUndefined(expected) ? true : expected;

      function onSettingLoaded(setting) {
        if (angular.equals(expected, setting)) {
          deferred.resolve();
        } else {
          deferred.reject(interpolate(
            gettext('Setting is not enabled: %(setting)s'),
            {setting: setting},
            true));
        }

        deferred.resolve(setting);
      }

      function onSettingFailure(message) {
        deferred.reject(message);
      }

      service.getSetting(setting, defaultSetting)
        .then(onSettingLoaded, onSettingFailure);

      return deferred.promise;
    }

  }
}());
