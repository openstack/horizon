/*
 * (c) Copyright 2015 Hewlett-Packard Development Company, L.P.
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
  'use strict';

  describe('Keystone API', function() {
    var testCall, service;
    var apiService = {};
    var toastService = {};

    beforeEach(
      module('horizon.mock.openstack-service-api',
        function($provide, initServices) {
          testCall = initServices($provide, apiService, toastService);
        })
    );

    beforeEach(module('horizon.app.core.openstack-service-api'));

    beforeEach(inject(['horizon.app.core.openstack-service-api.keystone', function(keystoneAPI) {
      service = keystoneAPI;
    }]));

    it('defines the service', function() {
      expect(service).toBeDefined();
    });

    var tests = [
      {
        "func": "getVersion",
        "method": "get",
        "path": "/api/keystone/version/",
        "error": "Unable to get the Keystone service version."
      },
      {
        "func": "getUsers",
        "method": "get",
        "path": "/api/keystone/users/",
        "data": {},
        "error": "Unable to retrieve the users."
      },
      {
        "func": "getUsers",
        "method": "get",
        "path": "/api/keystone/users/",
        "data": {
          "params": {
            "info": true
          }
        },
        "error": "Unable to retrieve the users.",
        "testInput": [
          {
            "info": true
          }
        ]
      },
      {
        "func": "createUser",
        "method": "post",
        "path": "/api/keystone/users/",
        "data": {
          "name": "Matt"
        },
        "error": "Unable to create the user.",
        "testInput": [
          {
            "name": "Matt"
          }
        ]
      },
      {
        "func": "deleteUsers",
        "method": "delete",
        "path": "/api/keystone/users/",
        "data": [
          1,
          2,
          3
        ],
        "error": "Unable to delete the users.",
        "testInput": [
          [
            1,
            2,
            3
          ]
        ]
      },
      {
        "func": "getCurrentUserSession",
        "method": "get",
        "path": "/api/keystone/user-session/",
        "data": "config",
        "error": "Unable to retrieve the current user session.",
        "testInput": [
          "config"
        ]
      },
      {
        "func": "getUser",
        "method": "get",
        "path": "/api/keystone/users/42",
        "error": "Unable to retrieve the user.",
        "testInput": [
          42
        ]
      },
      {
        "func": "editUser",
        "method": "patch",
        "path": "/api/keystone/users/42",
        "data": {
          "id": 42
        },
        "error": "Unable to edit the user.",
        "testInput": [
          {
            "id": 42
          }
        ]
      },
      {
        "func": "deleteUser",
        "method": "delete",
        "path": "/api/keystone/users/42",
        "error": "Unable to delete the user.",
        "testInput": [
          42
        ]
      },
      {
        "func": "getRoles",
        "method": "get",
        "path": "/api/keystone/roles/",
        "error": "Unable to retrieve the roles."
      },
      {
        "func": "createRole",
        "method": "post",
        "path": "/api/keystone/roles/",
        "data": "new role",
        "error": "Unable to create the role.",
        "testInput": [
          "new role"
        ]
      },
      {
        "func": "deleteRoles",
        "method": "delete",
        "path": "/api/keystone/roles/",
        "data": [
          1,
          2,
          3
        ],
        "error": "Unable to delete the roles.",
        "testInput": [
          [
            1,
            2,
            3
          ]
        ]
      },
      {
        "func": "getRole",
        "method": "get",
        "path": "/api/keystone/roles/42",
        "error": "Unable to retrieve the role.",
        "testInput": [
          42
        ]
      },
      {
        "func": "editRole",
        "method": "patch",
        "path": "/api/keystone/roles/42",
        "data": {
          "id": 42
        },
        "error": "Unable to edit the role.",
        "testInput": [
          {
            "id": 42
          }
        ]
      },
      {
        "func": "deleteRole",
        "method": "delete",
        "path": "/api/keystone/roles/42",
        "error": "Unable to delete the role.",
        "testInput": [
          42
        ]
      },
      {
        "func": "getDomains",
        "method": "get",
        "path": "/api/keystone/domains/",
        "error": "Unable to retrieve the domains."
      },
      {
        "func": "createDomain",
        "method": "post",
        "path": "/api/keystone/domains/",
        "data": "new domain",
        "error": "Unable to create the domain.",
        "testInput": [
          "new domain"
        ]
      },
      {
        "func": "deleteDomains",
        "method": "delete",
        "path": "/api/keystone/domains/",
        "data": [
          1,
          2,
          3
        ],
        "error": "Unable to delete the domains.",
        "testInput": [
          [
            1,
            2,
            3
          ]
        ]
      },
      {
        "func": "getDomain",
        "method": "get",
        "path": "/api/keystone/domains/42",
        "error": "Unable to retrieve the domain.",
        "testInput": [
          42
        ]
      },
      {
        "func": "editDomain",
        "method": "patch",
        "path": "/api/keystone/domains/42",
        "data": {
          "id": 42
        },
        "error": "Unable to edit the domain.",
        "testInput": [
          {
            "id": 42
          }
        ]
      },
      {
        "func": "deleteDomain",
        "method": "delete",
        "path": "/api/keystone/domains/42",
        "error": "Unable to delete the domain.",
        "testInput": [
          42
        ]
      },
      {
        "func": "getProjects",
        "method": "get",
        "path": "/api/keystone/projects/",
        "data": {},
        "error": "Unable to retrieve the projects."
      },
      {
        "func": "getProjects",
        "method": "get",
        "path": "/api/keystone/projects/",
        "data": {
          "params": {
            "info": true
          }
        },
        "error": "Unable to retrieve the projects.",
        "testInput": [
          {
            "info": true
          }
        ]
      },
      {
        "func": "createProject",
        "method": "post",
        "path": "/api/keystone/projects/",
        "data": "new project",
        "error": "Unable to create the project.",
        "testInput": [
          "new project"
        ]
      },
      {
        "func": "deleteProjects",
        "method": "delete",
        "path": "/api/keystone/projects/",
        "data": [
          1,
          2,
          3
        ],
        "error": "Unable to delete the projects.",
        "testInput": [
          [
            1,
            2,
            3
          ]
        ]
      },
      {
        "func": "getProject",
        "method": "get",
        "path": "/api/keystone/projects/42",
        "error": "Unable to retrieve the project.",
        "testInput": [
          42
        ]
      },
      {
        "func": "editProject",
        "method": "patch",
        "path": "/api/keystone/projects/42",
        "data": {
          "id": 42
        },
        "error": "Unable to edit the project.",
        "testInput": [
          {
            "id": 42
          }
        ]
      },
      {
        "func": "deleteProject",
        "method": "delete",
        "path": "/api/keystone/projects/42",
        "error": "Unable to delete the project.",
        "testInput": [
          42
        ]
      },
      {
        "func": "grantRole",
        "method": "put",
        "path": "/api/keystone/projects/42/32/22",
        "error": "Unable to grant the role.",
        "testInput": [
          42,
          32,
          22
        ]
      },
      {
        "func": "serviceCatalog",
        "method": "get",
        "path": "/api/keystone/svc-catalog/",
        "data": "config",
        "error": "Unable to fetch the service catalog.",
        "testInput": [
          "config"
        ]
      },
      {
        "func": "getServices",
        "method": "get",
        "path": "/api/keystone/services/",
        "error": "Unable to fetch the services."
      }
    ];

    // Iterate through the defined tests and apply as Jasmine specs.
    angular.forEach(tests, function(params) {
      it('defines the ' + params.func + ' call properly', function() {
        var callParams = [apiService, service, toastService, params];
        testCall.apply(this, callParams);
      });
    });

  });

})();
