/*
Copyright 2015, Hewlett-Packard Development Company, L.P.

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
*/
(function () {
  'use strict';

  /**
   * @ngdoc service
   * @name hz.api.SecurityGroup
   * @description Provides access to Security Groups
   */
  function SecurityGroup(apiService) {

    /**
     * @name hz.api.SecurityGroup.list
     * @description
     * Get a list of security groups.
     *
     * The listing result is an object with property "items". Each item is
     * an image.
     *
     * @example
     * The following is an example response:
     * {
     *     "items": [
     *         {
     *             "description": "Default security group",
     *             "id": "4a4c9dd4-ffa0-454a-beaa-23e8fa569062",
     *             "name": "default",
     *             "security_group_rules": [
     *                 {
     *                     "direction": "ingress",
     *                     "ethertype": "IPv4",
     *                     "id": "22961412-fba1-4d0d-8eb8-d4460c921346",
     *                     "port_range_max": null,
     *                     "port_range_min": null,
     *                     "protocol": null,
     *                     "remote_group_id": "4a4c9dd4-ffa0-454a-beaa-23e8fa569062",
     *                     "remote_ip_prefix": null,
     *                     "security_group_id": "4a4c9dd4-ffa0-454a-beaa-23e8fa569062",
     *                     "tenant_id": "3f867827f7eb45d4aa1d1395237f426b"
     *                 }
     *             ],
     *             "tenant_id": "3f867827f7eb45d4aa1d1395237f426b"
     *         }
     *     ]
     * }
     */
    this.query = function() {
      return apiService.get('/api/network/securitygroups/')
        .error(function () {
          horizon.alert('error', gettext('Unable to retrieve security groups.'));
      });
    };
  }

  // Register it with the API module so that anybody using the
  // API module will have access to the Security Group APIs.

  angular.module('hz.api')
    .service('securityGroup', ['apiService', SecurityGroup]);

}());
