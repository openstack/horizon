/*
 *    (c) Copyright 2015 Hewlett-Packard Development Company, L.P.
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

  /**
   * @ngdoc overview
   * @name horizon.dashboard.project.workflow.keypair.create-keypair-service
   *
   * @description
   * Service to handle creating keypairs and downloading their private keys.
   * Please note, the implementation has quirks due to what features are
   * available in which browsers.  As a result, the implementation involves
   * using iframes to specify downloads.  Since the API does not allow the
   * full retrieval of the key pair after creation, and the URL retrieved in
   * an iframe must be a GET method, and the fact that we shouldn't pass
   * data as part of the URL (because it is potentially logged and contains
   * private key data), we have to make the actual API call when performing
   * the GET.  This also means that if the user misses the download for some
   * reason, we need to provide the ability to regenerate the key pair,
   * although that is not a feature of this service.
   */

  angular
    .module('horizon.app.core.openstack-service-api')
    .factory('horizon.app.core.openstack-service-api.keypair-download-service',
      keypairDownloadService);

  keypairDownloadService.$inject = [
    '$document',
    'horizon.app.core.openstack-service-api.nova',
    '$q',
    '$timeout'
  ];

  function keypairDownloadService($document, novaAPI, $q, $timeout) {

    var service = {
      createAndDownloadKeypair: createAndDownloadKeypair
    };

    return service;

    /**
     * @ngdoc function
     * @name createAndDownloadKeypair
     *
     * @description
     * This function performs the actions necessary to begin a download
     * of a newly created key pair.  The given name will be used as the
     * logical name of the key pair and will be used to make a file-system-
     * friendly filename.
     * In this implementation, for browser compatibility reasons, the
     * download is achieved by creating an iframe with the given path for
     * the create API call given, so the results are streamed directly to the
     * client.  This is not ideal but is due to lack of support in IE for
     * features like the data: protocol.  The iframes require that an element
     * with the class of 'download-iframes' is present.
     *
     * @param {string} name The desired name for the key pair
     */
    function createAndDownloadKeypair(name) {
      addDOMResource(name);
      return verifyCreatedPromise(name);
    }

    /**
     * @ngdoc function
     * @name addDOMResource
     *
     * @description
     * This adds an iframe to the body of the current document, using
     * the appropriate URL for the API to create/download the new key pair.
     *
     * @param {string} keypairName The desired name for the key pair
     */
    function addDOMResource(keypairName) {
      var url = novaAPI.getCreateKeypairUrl(keypairName);
      var iframe = angular.element("<iframe></iframe>");
      iframe.attr('id', keypairName);
      iframe.attr('src', url);
      iframe.attr('style', 'display: none;');
      if ($document.find('.download-iframes').size() === 0) {
        var iframeContainer = angular.element('<div class="download-iframes"></div>');
        $document.find('body').append(iframeContainer);
      }
      $document.find('.download-iframes').append(iframe);
    }

    /**
     * @ngdoc function
     * @name verifyCreatedPromise
     *
     * @description
     * This function returns a promise that tries ten times to see if a
     * key pair of the given name exists in the key pair listing.  These
     * tries are one second apart.  Once it has been found, the promise
     * is resolved with the key pair data.  If it is not found within the
     * period, the promise is rejected.
     *
     * @param {string} name The name for the key pair
     */
    function verifyCreatedPromise(name) {
      return $q(function doesKeypairExistPromise(resolve, reject) {

        doesKeypairExist(10);

        function doesKeypairExist(timesToCheck) {
          $timeout(function doesKeypairExistTimeout() {
            novaAPI.getKeypairs().then(function isKeypairInResponse(response) {

              var foundKeypairs = response.data.items.filter(function sameName(item) {
                return item.keypair.name === name;
              });

              if (foundKeypairs.length === 1) {
                resolve(foundKeypairs[0].keypair);
                angular.element('.download-iframes #' + name).remove();
              } else if (timesToCheck > 1) {
                doesKeypairExist(timesToCheck - 1);
              } else {
                reject();
                angular.element('.download-iframes #' + name).remove();
              }

            });
          },
          1000);
        }

      });
    }

  }

})();
