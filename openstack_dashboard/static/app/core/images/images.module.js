/**
 * (c) Copyright 2015 Hewlett-Packard Development Company, L.P.
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

  /**
   * @ngdoc overview
   * @ngname horizon.app.core.images
   *
   * @description
   * Provides all of the services and widgets required
   * to support and display images related content.
   */
  angular
    .module('horizon.app.core.images', ['ngRoute', 'horizon.app.core.images.actions'])
    .constant('horizon.app.core.images.events', events())
    .constant('horizon.app.core.images.non_bootable_image_types', ['aki', 'ari'])
    .constant('horizon.app.core.images.resourceType', 'OS::Glance::Image')
    .config(config);

  /**
   * @ngdoc value
   * @name horizon.app.core.images.events
   * @description a list of events for images
   */
  function events() {
    return {
      DELETE_SUCCESS: 'horizon.app.core.images.DELETE_SUCCESS',
      VOLUME_CHANGED: 'horizon.app.core.images.VOLUME_CHANGED',
      UPDATE_METADATA_SUCCESS: 'horizon.app.core.images.UPDATE_METADATA_SUCCESS'
    };
  }

  config.$inject = [
    '$provide',
    '$windowProvider',
    '$routeProvider'
  ];

  /**
   * @name horizon.app.core.images.tableRoute
   * @name horizon.app.core.images.detailsRoute
   * @description Routes used by this module.
   */
  function config($provide, $windowProvider, $routeProvider) {
    var path = $windowProvider.$get().STATIC_URL + 'app/core/images/';
    $provide.constant('horizon.app.core.images.basePath', path);
    var tableUrl = path + "table/";
    var projectTableRoute = 'project/ngimages/';
    var detailsUrl = path + "detail/";
    var projectDetailsRoute = 'project/ngimages/details/';

    // Share the routes as constants so that views within the images module
    // can create links to each other.
    $provide.constant('horizon.app.core.images.tableRoute', projectTableRoute);
    $provide.constant('horizon.app.core.images.detailsRoute', projectDetailsRoute);

    $routeProvider
      .when('/' + projectTableRoute, {
        templateUrl: tableUrl + 'images-table.html'
      })
      .when('/' + projectDetailsRoute + ':imageId', {
        templateUrl: detailsUrl + 'image-detail.html'
      });
  }

})();
