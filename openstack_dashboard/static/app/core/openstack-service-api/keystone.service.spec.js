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
    var testCall, service, settings;
    var apiService = {};
    var toastService = {};

    beforeEach(
      module('horizon.mock.openstack-service-api',
        function($provide, initServices) {
          testCall = initServices($provide, apiService, toastService);
        })
    );

    beforeEach(module('horizon.app.core.openstack-service-api'));

    beforeEach(inject(function($injector) {
      service = $injector.get('horizon.app.core.openstack-service-api.keystone');
      settings = $injector.get('horizon.app.core.openstack-service-api.settings');
    }));

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
        "func": "getDefaultDomain",
        "method": "get",
        "path": "/api/keystone/default_domain/",
        "error": "Unable to retrieve the default domain."
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
      },
      {
        "func": "getGroups",
        "method": "get",
        "path": "/api/keystone/groups/",
        "error": "Unable to fetch the groups."
      },
      {
        "func": "createGroup",
        "method": "post",
        "path": "/api/keystone/groups/",
        "data": "new group",
        "error": "Unable to create the group.",
        "testInput": [
          "new group"
        ]
      },
      {
        "func": "getGroup",
        "method": "get",
        "path": "/api/keystone/groups/14",
        "error": "Unable to retrieve the group.",
        "testInput": [
          14
        ]
      },
      {
        "func": "editGroup",
        "method": "patch",
        "path": "/api/keystone/groups/42",
        "data": {
          "id": 42
        },
        "error": "Unable to edit the group.",
        "testInput": [
          {
            "id": 42
          }
        ]
      },
      {
        "func": "deleteGroup",
        "method": "delete",
        "path": "/api/keystone/groups/14",
        "error": "Unable to delete the group.",
        "testInput": [
          14
        ]
      },
      {
        "func": "deleteGroups",
        "method": "delete",
        "path": "/api/keystone/groups/",
        "data": [
          1,
          2,
          3
        ],
        "error": "Unable to delete the groups.",
        "testInput": [
          [
            1,
            2,
            3
          ]
        ]
      }
    ];

    // Iterate through the defined tests and apply as Jasmine specs.
    angular.forEach(tests, function(params) {
      it('defines the ' + params.func + ' call properly', function() {
        var callParams = [apiService, service, toastService, params];
        testCall.apply(this, callParams);
      });
    });

    describe('Keystone API Helpers', function () {
      var deferred, $timeout;

      beforeEach(inject(function (_$q_, _$timeout_) {
        deferred = _$q_.defer();
        $timeout = _$timeout_;
      }));

      describe('getProjectName', function () {

        var project = {
          id: 'projectID',
          name: 'projectName'
        };

        it("it returns the project name when it exists", function () {
          deferred.resolve({data: project});
          spyOn(service, 'getProject').and.returnValue(deferred.promise);
          service.getProjectName(project.id).then(expectName);
          $timeout.flush();
          expect(service.getProject).toHaveBeenCalledWith(project.id);
        });

        it("it returns the project id when name doesn't exist", function () {
          deferred.resolve({data: {id: project.id}});
          spyOn(service, 'getProject').and.returnValue(deferred.promise);
          service.getProjectName(project.id).then(expectID);
          $timeout.flush();
          expect(service.getProject).toHaveBeenCalledWith(project.id);
        });

        function expectName(name) {
          expect(name).toBe(project.name);
        }

        function expectID(name) {
          expect(name).toBe(project.id);
        }
      });

    });

    describe('canEditIdentity', function () {
      var deferred, $timeout;

      beforeEach(inject(function (_$q_, _$timeout_) {
        deferred = _$q_.defer();
        $timeout = _$timeout_;
      }));

      it('should resolve true if can_edit_group is set True', function() {
        deferred.resolve({can_edit_group: true});
        spyOn(settings, 'getSettings').and.returnValue(deferred.promise);
        var canEdit = service.canEditIdentity('group');
        $timeout.flush();
        expect(canEdit).toBeTruthy();
      });

      it('should resolve false if can_edit_group is set False', function() {
        deferred.resolve({can_edit_group: false});
        spyOn(settings, 'getSettings').and.returnValue(deferred.promise);
        var canEdit = service.canEditIdentity('group');
        $timeout.flush();
        // reject
        expect(canEdit.$$state.status).toEqual(2);
      });
    });
  });
})();
