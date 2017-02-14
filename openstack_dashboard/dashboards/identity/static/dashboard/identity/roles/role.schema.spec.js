/**
 * Copyright 2016 Rackspace
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
(function () {
  'use strict';

  describe('horizon.dashboard.identity.roles.role.schema', function () {
    var schema;

    beforeEach(module('horizon.app.core.openstack-service-api'));
    beforeEach(module('horizon.dashboard.identity'));
    beforeEach(module('horizon.framework'));
    beforeEach(inject(function($injector) {
      schema = $injector.get('horizon.dashboard.identity.roles.role-schema');
    }));

    it('should define a name property', function() {
      expect(schema.properties.name).toBeDefined();
    });
  });
})();
