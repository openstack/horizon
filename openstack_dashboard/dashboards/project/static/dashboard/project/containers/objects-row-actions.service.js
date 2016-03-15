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

(function() {
  'use strict';

  angular
    .module('horizon.dashboard.project.containers')
    .factory('horizon.dashboard.project.containers.objects-row-actions', rowActions)
    .factory('horizon.dashboard.project.containers.objects-actions.delete', deleteService)
    .factory('horizon.dashboard.project.containers.objects-actions.download', downloadService)
    .factory('horizon.dashboard.project.containers.objects-actions.view', viewService);

  rowActions.$inject = [
    'horizon.dashboard.project.containers.basePath',
    'horizon.dashboard.project.containers.objects-actions.delete',
    'horizon.dashboard.project.containers.objects-actions.download',
    'horizon.dashboard.project.containers.objects-actions.view',
    'horizon.framework.util.i18n.gettext'
  ];

  /**
   * @ngdoc factory
   * @name horizon.app.core.images.table.row-actions.service
   * @description A list of row actions.
   */
  function rowActions(
    basePath,
    deleteService,
    downloadService,
    viewService,
    gettext
  ) {
    return {
      actions: actions
    };

    ///////////////

    function actions() {
      return [
        {
          service: downloadService,
          template: {text: gettext('Download'), type: 'link'}
        },
        {
          service: viewService,
          template: {text: gettext('View Details')}
        },
        {
          service: deleteService,
          template: {text: gettext('Delete'), type: 'delete'}
        }
      ];
    }
  }

  downloadService.$inject = [
    'horizon.framework.util.q.extensions'
  ];

  function downloadService($qExtensions) {
    return {
      allowed: function allowed(file) { return $qExtensions.booleanAsPromise(file.is_object); },
      perform: function perform(file) { return file.url; }
    };
  }

  viewService.$inject = [
    'horizon.app.core.openstack-service-api.swift',
    'horizon.dashboard.project.containers.basePath',
    'horizon.dashboard.project.containers.containers-model',
    'horizon.framework.util.q.extensions',
    '$modal'
  ];

  function viewService(swiftAPI, basePath, model, $qExtensions, $modal) {
    return {
      allowed: function allowed(file) {
        return $qExtensions.booleanAsPromise(file.is_object);
      },
      perform: function perform(file) {
        var objectPromise = swiftAPI.getObjectDetails(
          model.container.name,
          model.fullPath(file.name)
        ).then(
          function received(response) {
            return response.data;
          }
        );
        var localSpec = {
          backdrop: 'static',
          controller: 'SimpleModalController as ctrl',
          templateUrl: basePath + 'object-details-modal.html',
          resolve: {
            context: function context() { return objectPromise; }
          }
        };

        $modal.open(localSpec);
      }
    };
  }

  deleteService.$inject = [
    'horizon.dashboard.project.containers.containers-model',
    'horizon.framework.util.q.extensions',
    'horizon.framework.widgets.modal.simple-modal.service',
    'horizon.framework.widgets.toast.service'
  ];

  function deleteService(model, $qExtensions, simpleModalService, toastService) {
    var service = {
      allowed: function allowed() {
        return $qExtensions.booleanAsPromise(true);
      },
      perform: function perform(file) {
        var options = {
          title: gettext('Confirm Delete'),
          body: interpolate(
            gettext('Are you sure you want to delete %(name)s?'), file, true
          ),
          submit: gettext('Yes'),
          cancel: gettext('No')
        };

        simpleModalService.modal(options).result.then(function confirmed() {
          return service.deleteServiceAction(file);
        });
      },
      deleteServiceAction: deleteServiceAction
    };

    return service;

    function deleteServiceAction(file) {
      return model.deleteObject(file).then(function success() {
        model.updateContainer();
        return toastService.add('success', interpolate(
          gettext('%(name)s deleted.'), {name: file.name}, true
        ));
      });
    }
  }
})();
