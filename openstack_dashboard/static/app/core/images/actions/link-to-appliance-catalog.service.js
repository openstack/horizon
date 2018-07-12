/**
 *
 * Licensed under the Apache License, Version 2.0 (the "License"); you may
 * not use self file except in compliance with the License. You may obtain
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
  
    angular
      .module('horizon.app.core.images')
      .factory('horizon.app.core.images.actions.link-to-appliance-catalog.service', linkToApplianceCatalogService);
  
    linkToApplianceCatalogService.$inject = [
      '$q',
      'horizon.app.core.openstack-service-api.glance',
      'horizon.app.core.openstack-service-api.userSession',
      'horizon.app.core.images.non_bootable_image_types',
      'horizon.dashboard.project.workflow.launch-instance.modal.service',
      'horizon.framework.util.q.extensions',
      'horizon.app.core.openstack-service-api.policy'
    ];
  
    /**
     * @ngDoc factory
     * @name horizon.app.core.images.actions.linkToApplianceCatalogService
     * @param {Object} $q
     * @param {Object} nonBootableImageTypes
     * @param {Object} launchInstanceModal
     * @param {Object} $qExtensions
     * @Description
     * Brings up the Launch Instance for image modal.
     * On submit, launch the instance for the Image.
     * On cancel, do nothing.
     *
     * @returns {Object} The service
     */
    function linkToApplianceCatalogService(
      $q,
      glance,
      userSessionService,
      nonBootableImageTypes,
      launchInstanceModal,
      $qExtensions
    ) {
      var service = {
        perform: perform,
        allowed: allowed
      };
      var modifyImagePolicyCheck, scope;
  
      return service;

      function initScope($scope) {
        scope = $scope;
        $scope.$on(events.IMAGE_METADATA_CHANGED, onMetadataChange);
        modifyImagePolicyCheck = policy.ifAllowed({rules: [['image', 'modify_image']]});
      }

      function allowed(image){
        
        return $q.all([
            applianceCatalogEntryExists(image),
            isActive(image)
          ]);
      }

      //////////////
  
      function perform(image) {
        // Previous uses of this relocated the display using the successUrl;
        // in this case we leave the post-action behavior up to the result
        // handler.
        return window.open(image.appliance_catalog_host + image.appliance_catalog_details_path + '/' + image.appliance_catalog_id);
      }
  
      function isActive(image) {
        return $qExtensions.booleanAsPromise(image.status === 'active');
      }

      function applianceCatalogEntryExists(image){
        return $qExtensions.booleanAsPromise(image.appliance_catalog_id != -1);
      }
  
      function isBootable(image) {
        return $qExtensions.booleanAsPromise(
          nonBootableImageTypes.indexOf(image.container_format) < 0
        );
      }
  
    } // end of linkToApplianceCatalogService
  })(); // end of IIFE
  