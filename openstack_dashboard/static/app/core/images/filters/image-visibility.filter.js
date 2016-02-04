/**
 * (c) Copyright 2016 Hewlett-Packard Development Company, L.P.
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
    .module('horizon.app.core.images')
    .filter('imageVisibility', imageVisibilityFilter);

  imageVisibilityFilter.$inject = [
    'horizon.framework.util.i18n.gettext'
  ];

  /**
   * @ngdoc filter
   * @name imageVisibilityFilter
   * @description
   * Takes a raw image object from the API and returns the user friendly
   * visibility. Handles both v1 (is_public) and v2 (visibility).
   *
   * @param {Object} image - Image object from the glance API.
   * @param {string} currentProjectId (optional) Pass this in if the filter should derive the
   * sharing status based on the current project id. If the image is non-public and the image
   * is not "owned" by the current project, then this will return a visibility of "Shared with Me".
   *
   * @example
   *
   * Get an image object from the api:
   *
   * horizon.app.core.openstack-service-api.glance
   *
   * In HTML, pass the image to the filter:
   *
   * {$ image | imageVisibility $}
   *
   * In javascript, use it like this:
   *
   * var visibility = imageVisibilityFilter(image);
   *
   * Or, to include deriving the shared with me status:
   *
   * var visibility = imageVisibilityFilter(image, currentProjectId);
   */
  function imageVisibilityFilter(gettext) {
    var imageVisibility = {
      'public': gettext('Public'),
      'private': gettext('Private'),
      'shared_with_me': gettext('Shared with Me'),
      'unknown': gettext('Unknown')
    };

    return function getVisibility(image, currentProjectId) {
      if (null !== image && angular.isDefined(image)) {
        return evaluateImageProperties(image, currentProjectId);
      } else {
        return imageVisibility.unknown;
      }
    };

    function evaluateImageProperties(image, currentProjectId) {
      // visibility property is preferred over is_public property
      var translatedVisibility;
      if (angular.isDefined(image.visibility)) {
        translatedVisibility = safeTranslateVisibility(image.visibility);
      } else if (angular.isDefined(image.is_public)) {
        translatedVisibility = translateIsPublic(image.is_public);
      } else {
        // If neither are defined, we still want something displayable
        translatedVisibility = imageVisibility.unknown;
      }

      return deriveSharingStatus(image, currentProjectId, translatedVisibility);
    }

    function safeTranslateVisibility(visibility) {
      // Rather than show a default visibility when the visibility is not found
      // this will show the untranslated visibility. This allows the code
      // to be more forgiving if a new status is added to images and the UI
      // code isn't immediately updated.
      var translation = imageVisibility[visibility];
      if (angular.isDefined(translation)) {
        return translation;
      } else {
        return visibility;
      }
    }

    function translateIsPublic(isPublic) {
      if (isPublic) {
        return imageVisibility.public;
      } else {
        return imageVisibility.private;
      }
    }

    function deriveSharingStatus(image, currentProjectId, translatedVisibility) {
      if (angular.equals(translatedVisibility, imageVisibility.public)) {
        return translatedVisibility;
      } else if (angular.isDefined(currentProjectId) &&
        !angular.equals(image.owner, currentProjectId)) {
        return imageVisibility.shared_with_me;
      } else {
        return translatedVisibility;
      }
    }

  }

}());
