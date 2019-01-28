/*
 *    (c) Copyright 2016 Rackspace US, Inc
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
   * @ngdoc controller
   *
   * @name horizon.dashboard.project.containers.ContainersController
   *
   * @description
   * Controller for the interface around a list of containers for a single account.
   */
  angular
    .module('horizon.dashboard.project.containers')
    .controller('horizon.dashboard.project.containers.ContainersController', ContainersController);

  ContainersController.$inject = [
    'horizon.app.core.openstack-service-api.swift',
    'horizon.dashboard.project.containers.containers-model',
    'horizon.dashboard.project.containers.basePath',
    'horizon.dashboard.project.containers.baseRoute',
    'horizon.dashboard.project.containers.containerRoute',
    'horizon.framework.widgets.form.ModalFormService',
    'horizon.framework.widgets.modal.simple-modal.service',
    'horizon.framework.widgets.toast.service',
    'horizon.framework.widgets.magic-search.events',
    'horizon.framework.widgets.magic-search.service',
    '$scope',
    '$location',
    '$q'
  ];

  function ContainersController(swiftAPI,
                                containersModel,
                                basePath,
                                baseRoute,
                                containerRoute,
                                modalFormService,
                                simpleModalService,
                                toastService,
                                magicSearchEvents,
                                magicSearchService,
                                $scope,
                                $location,
                                $q) {
    var ctrl = this;
    ctrl.model = containersModel;
    ctrl.model.initialize();
    ctrl.baseRoute = baseRoute;
    ctrl.containerRoute = containerRoute;
    ctrl.filterFacets = [
      {
        name: 'prefix',
        label: gettext('Prefix'),
        singleton: true,
        isServer: true
      }];

    // TODO(lcastell): remove this flag when the magic search bar can be used
    // as an standalone component.
    // This flag is used to tell what trigger the search updated event. Currently,
    // when selecting a container the magic-search controller gets executed and emits
    // the searchUpdated event.
    ctrl.filterEventTrigeredBySearchBar = true;

    ctrl.checkContainerNameConflict = checkContainerNameConflict;
    ctrl.toggleAccess = toggleAccess;
    ctrl.deleteContainer = deleteContainer;
    ctrl.deleteContainerAction = deleteContainerAction;
    ctrl.createContainer = createContainer;
    ctrl.createContainerAction = createContainerAction;
    ctrl.selectContainer = selectContainer;

    //////////
    function checkContainerNameConflict(containerName) {
      if (!containerName) {
        // consider empty model valid
        return $q.when();
      }

      var def = $q.defer();
      // reverse the sense here - successful lookup == error so we reject the
      // name if we find it in swift
      swiftAPI.getContainer(containerName, true).then(def.reject, def.resolve);
      return def.promise;
    }

    function selectContainer(container) {
      if (!ctrl.model.container || container.name !== ctrl.model.container.name) {
        ctrl.filterEventTrigeredBySearchBar = false;
      }
      ctrl.model.container = container;
      $location.path(ctrl.containerRoute + container.name);

      return ctrl.model.fetchContainerDetail(container);
    }

    function toggleAccess(container) {
      swiftAPI.setContainerAccess(container.name, container.is_public).then(
        function updated() {
          var access = 'private';
          if (container.is_public) {
            access = 'public';
          }
          toastService.add('success', interpolate(
            gettext('Container %(name)s is now %(access)s.'),
            {name: container.name, access: access},
            true
          ));

          // re-fetch container details
          ctrl.model.fetchContainerDetail(container, true);
        },
        function failure() {
          container.is_public = !container.is_public;
        });
    }

    function deleteContainer(container) {
      var options = {
        title: gettext('Confirm Delete'),
        body: interpolate(
          gettext('Are you sure you want to delete container %(name)s?'), container, true
        ),
        submit: gettext('Delete'),
        cancel: gettext('Cancel'),
        confirmCssClass: "btn-danger"
      };

      simpleModalService.modal(options).result.then(function confirmed() {
        return ctrl.deleteContainerAction(container);
      });
    }

    function deleteContainerAction(container) {
      swiftAPI.deleteContainer(container.name).then(
        function deleted() {
          toastService.add('success', interpolate(
            gettext('Container %(name)s deleted.'), container, true
          ));

          // remove the deleted container from the containers list
          for (var i = ctrl.model.containers.length - 1; i >= 0; i--) {
            if (ctrl.model.containers[i].name === container.name) {
              ctrl.model.containers.splice(i, 1);
              break;
            }
          }

          // route back to no selected container if we deleted the current one
          if (ctrl.model.container.name === container.name) {
            $location.path(ctrl.baseRoute);
          }
        });
    }

    var createContainerSchema = {
      type: 'object',
      properties: {
        name: {
          title: gettext('Container Name'),
          type: 'string',
          pattern: '^[^/]+$',
          description: gettext('Container name must not contain "/".')
        },
        public: {
          title: gettext('Container Access'),
          type: 'boolean',
          default: false,
          description:  gettext('A Public Container will allow anyone with the Public URL to ' +
            'gain access to your objects in the container.')
        }
      },
      required: ['name']
    };

    var createContainerForm = [
      {
        type: 'section',
        htmlClass: 'row',
        items: [
          {
            type: 'section',
            htmlClass: 'col-sm-12',
            items: [
              {
                key: 'name',
                validationMessage: {
                  exists: gettext('A container with that name exists.')
                },
                $asyncValidators: {
                  exists: checkContainerNameConflict
                }
              },
              {
                key: 'public',
                type: 'radiobuttons',
                disableSuccessState: true,
                titleMap: [
                  { value: true, name: gettext('Public') },
                  { value: false, name: gettext('Not public') }
                ]
              }
            ]
          }
        ]
      }
    ];

    function createContainer() {
      var model = {public: false};
      var config = {
        title: gettext('Create Container'),
        schema: createContainerSchema,
        form: createContainerForm,
        model: model,
        size: 'md',
        helpUrl: basePath + 'create-container.help.html'
      };
      return modalFormService.open(config).then(function then() {
        return ctrl.createContainerAction(model);
      });
    }

    function createContainerAction(model) {
      return swiftAPI.createContainer(model.name, model.public).then(
        function success() {
          toastService.add('success', interpolate(
            gettext('Container %(name)s created.'), model, true
          ));
          // generate a table row with no contents
          ctrl.model.containers.push({name: model.name, count: 0, bytes: 0});
        }
      );
    }
    $scope.$on(magicSearchEvents.SEARCH_UPDATED, function(event, data) {
      // At this moment there's only server side filtering supported, therefore
      // there's no need to check if it is client side or server side filtering
      if (ctrl.filterEventTrigeredBySearchBar) {
        ctrl.model.getContainers(magicSearchService.getQueryObject(data));
      }
      else {
        ctrl.filterEventTrigeredBySearchBar = true;
      }
    });
  }
})();
