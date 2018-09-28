/*
 * (c) Copyright 2016 Hewlett Packard Enterprise Development Company LP
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

  describe('horizon.framework.util.navigations.service', function() {
    var service, navigations, spyElement;
    var imagesUrl = '/project/images/';
    var breadcrumb = ['Project', 'Compute', 'Images'];
    var breadcrumbWithoutGroup = ['Project', 'Images'];

    function getNavsElement (selector) {
      try {
        // for searching element
        return navigations.find(selector);
      } catch (e) {
        // for creating element
        return $(selector);
      }
    }

    beforeEach(module('horizon.framework.util.navigations'));

    beforeEach(inject(function($injector) {
      service = $injector.get('horizon.framework.util.navigations.service');
      navigations = angular.element(
        '<div>' +
        '  <!-- navigation side bar -->' +
        '  <li class="openstack-dashboard">' +
        '    <a class="" aria-expanded="true">' +
        '      Project' +
        '    </a>' +
        '    <ul class="in" style="">' +
        '      <li class="openstack-panel-group">' +
        '        <a class="" area-expanded="true">' +
        '          Compute' +
        '        </a>' +
        '        <div class="in" style="">' +
        '          <a class="openstack-panel active" href="/project/images/">' +
        '            Images' +
        '          </a>' +
        '        </div>' +
        '      </li>' +
        '    </ul>' +
        '  </li>' +
        '  <!-- breadcrumb -->' +
        '  <div class="page-breadcrumb">' +
        '    <ol class="breadcrumb">' +
        '      <li>Project</li>' +
        '      <li>Compute</li>' +
        '      <li class="active">Images</li>' +
        '    </ol>' +
        '  </div>' +
        '</div>');
      spyElement = spyOn(angular, 'element').and.callFake(getNavsElement);
    }));

    afterEach(function() {
      spyElement.and.callThrough();
    });

    describe('getActivePanelUrl', function() {
      it('returns an empty array if no items', function() {
        var activeUrl = service.getActivePanelUrl();

        expect(activeUrl).toBe(imagesUrl);
      });
    });

    describe('collapseAllNavigation', function() {
      it('collapse all nodes on navigation side bar', function() {
        service.collapseAllNavigation();

        var hasIn = navigations.find('.in');
        expect(hasIn.length).toBe(0);
        var collapsed = navigations.find('a.collapsed[aria-expanded=false]');
        expect(collapsed.length).toBe(2);
        var hasActive = navigations.find('a.openstack-panel.active');
        expect(hasActive.length).toBe(0);
      });
    });

    describe('expandNavigationByUrl', function() {
      it('expands navigation side bar and return their label of selected nodes', function() {
        spyOn(service, 'collapseAllNavigation').and.callThrough();
        var list = service.expandNavigationByUrl(imagesUrl);

        expect(list).toEqual(breadcrumb);

        var hasIn = navigations.find('.in');
        expect(hasIn.length).toBe(2);
        var expanded = navigations.find('a[aria-expanded=true]');
        expect(expanded.length).toBe(2);
        var hasActive = navigations.find('a.openstack-panel.active');
        expect(hasActive.length).toBe(1);
      });
    });

    describe('expandNavigationByUrl', function() {
      it('expands navigation side bar without panelgroup' +
         'and return their label of selected nodes', function() {
        navigations = angular.element(
            '<div>' +
            '  <!-- navigation side bar -->' +
            '  <li class="openstack-dashboard">' +
            '    <a class="" aria-expanded="true">' +
            '      Project' +
            '    </a>' +
            '    <ul class="in" style="">' +
            '      <div class="in" style="">' +
            '        <a class="openstack-panel active" href="/project/images/">' +
            '          Images' +
            '        </a>' +
            '      </div>' +
            '    </ul>' +
            '  </li>' +
            '  <!-- breadcrumb -->' +
            '  <div class="page-breadcrumb">' +
            '    <ol class="breadcrumb">' +
            '      <li>Project</li>' +
            '      <li>Compute</li>' +
            '      <li class="active">Images</li>' +
            '    </ol>' +
            '  </div>' +
            '</div>');

        spyOn(service, 'collapseAllNavigation').and.callThrough();
        var list = service.expandNavigationByUrl(imagesUrl);

        expect(list).toEqual(breadcrumbWithoutGroup);

        var hasIn = navigations.find('.in');
        expect(hasIn.length).toBe(2);
        var expanded = navigations.find('a[aria-expanded=true]');
        expect(expanded.length).toBe(1);
        var hasActive = navigations.find('a.openstack-panel.active');
        expect(hasActive.length).toBe(1);
      });
    });

    describe('setBreadcrumb', function() {
      it('sets breadcrumb items from specified array', function() {
        service.setBreadcrumb(breadcrumb);
      });
    });

    describe('isNavigationExists', function() {
      it('returns true if navigation for specified URL exists', function() {
        var result = service.isNavigationExists('/project/images/');
        expect(result).toEqual(true);
      });

      it('returns false if navigation for specified URL does not exist', function() {
        var result = service.isNavigationExists('/not/found/');
        expect(result).toEqual(false);
      });
    });

  });

})();
