/*
 * (c) Copyright 2016 Hewlett Packard Enterprise Development LP
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
(function() {
  "use strict";

  angular.module('horizon.app.core.images')
    .factory('horizon.app.core.images.service', imageService);

  imageService.$inject = [
    'horizon.app.core.openstack-service-api.glance',
    'horizon.app.core.images.transitional-statuses'
  ];

  /*
   * @ngdoc factory
   * @name horizon.app.core.images.service
   *
   * @description
   * This service provides functions that are used through the Images
   * features.  These are primarily used in the module registrations
   * but do not need to be restricted to such use.  Each exposed function
   * is documented below.
   */
  function imageService(glance, transitionalStatuses) {
    return {
      getDetailsPath: getDetailsPath,
      getImagesPromise: getImagesPromise,
      imageType: imageType,
      isInTransition: isInTransition
    };

    /*
     * @ngdoc function
     * @name getDetailsPath
     * @param item {Object} - The image object
     * @description
     * Given an Image object, returns the relative path to the details
     * view.
     */
    function getDetailsPath(item) {
      return 'project/ngdetails/OS::Glance::Image/' + item.id;
    }

    /*
     * @ngdoc function
     * @name imageType
     * @param item {Object} - The image object
     * @description
     * Given an Image object, returns a name describing the type of image,
     * either an 'Image' or a 'Snapshot' type.
     */
    function imageType(item) {
      if (null !== item &&
        angular.isDefined(item) &&
        angular.isDefined(item.properties) &&
        item.properties.image_type === 'snapshot') {
        return gettext('Snapshot');
      } else {
        return gettext('Image');
      }
    }

    /**
     * @ngdoc function
     * @name isInTransition
     * @param item {object} - The image object
     * @description
     * Given an Image object, returns a boolean representing whether the image
     * is in a transitional state.
     * @returns {boolean}
     */
    function isInTransition(item) {
      if (item && angular.isString(item.status)) {
        return transitionalStatuses.indexOf(item.status.toLowerCase()) > -1;
      }
      return false;
    }

    /*
     * @ngdoc function
     * @name getImagesPromise
     * @description
     * Given filter/query parameters, returns a promise for the matching
     * images.  This is used in displaying lists of Images.  In this case,
     * we need to modify the API's response by adding a composite value called
     * 'trackBy' to assist the display mechanism when updating rows.
     */
    function getImagesPromise(params) {
      return glance.getImages(params).then(modifyResponse);

      function modifyResponse(response) {
        return {data: {items: response.data.items.map(addTrackBy)}};

        function addTrackBy(image) {
          image.trackBy = image.id + image.updated_at;
          return image;
        }
      }
    }
  }

})();
