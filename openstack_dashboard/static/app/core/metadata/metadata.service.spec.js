/*
 * Copyright 2015, ThoughtWorks Inc.
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

  describe('metadata.service', function () {

    beforeEach(module('horizon.app.core.metadata'));

    var nova = {getAggregateExtraSpecs: function() {},
                getFlavorExtraSpecs: function() {},
                editAggregateExtraSpecs: function() {},
                editFlavorExtraSpecs: function() {},
                getInstanceMetadata: function() {},
                editInstanceMetadata: function() {} };

    var glance = {getImageProps: function() {},
                  editImageProps: function() {},
                  getNamespaces: function() {}};

    var cinder = {getVolumeMetadata:function() {},
                  getVolumeSnapshotMetadata:function() {},
                  getVolumeTypeMetadata:function() {},
                  editVolumeMetadata: function() {},
                  editVolumeSnapshotMetadata: function() {}};

    beforeEach(function() {
      module(function($provide) {
        $provide.value('horizon.app.core.openstack-service-api.nova', nova);
        $provide.value('horizon.app.core.openstack-service-api.glance', glance);
        $provide.value('horizon.app.core.openstack-service-api.cinder', cinder);
      });
    });

    var metadataService;

    beforeEach(inject(function($injector) {
      metadataService = $injector.get('horizon.app.core.metadata.service');
    }));

    it('should get aggregate metadata', function() {
      var expected = 'aggregate metadata';
      spyOn(nova, 'getAggregateExtraSpecs').and.returnValue(expected);
      var actual = metadataService.getMetadata('aggregate', '1');
      expect(actual).toBe(expected);
    });

    it('should edit aggregate metadata', function() {
      spyOn(nova, 'editAggregateExtraSpecs');
      metadataService.editMetadata('aggregate', '1', 'updated', ['removed']);
      expect(nova.editAggregateExtraSpecs).toHaveBeenCalledWith('1', 'updated', ['removed']);
    });

    it('should get aggregate namespace', function() {
      spyOn(glance, 'getNamespaces');
      metadataService.getNamespaces('aggregate');
      expect(glance.getNamespaces)
      .toHaveBeenCalledWith({ resource_type: 'OS::Nova::Aggregate' }, false);
    });

    it('should get flavor metadata', function() {
      var expected = 'flavor metadata';
      spyOn(nova, 'getFlavorExtraSpecs').and.returnValue(expected);
      var actual = metadataService.getMetadata('flavor', '1');
      expect(actual).toBe(expected);
    });

    it('should edit flavor metadata', function() {
      spyOn(nova, 'editFlavorExtraSpecs');
      metadataService.editMetadata('flavor', '1', 'updated', ['removed']);
      expect(nova.editFlavorExtraSpecs).toHaveBeenCalledWith('1', 'updated', ['removed']);
    });

    it('should get flavor namespace', function() {
      spyOn(glance, 'getNamespaces');
      metadataService.getNamespaces('flavor');
      expect(glance.getNamespaces)
      .toHaveBeenCalledWith({ resource_type: 'OS::Nova::Flavor' }, false);
    });

    it('should get image metadata', function() {
      var expected = 'image metadata';
      spyOn(glance, 'getImageProps').and.returnValue(expected);
      var actual = metadataService.getMetadata('image', '1');
      expect(actual).toBe(expected);
    });

    it('should edit image metadata', function() {
      spyOn(glance, 'editImageProps');
      metadataService.editMetadata('image', '1', 'updated', ['removed']);
      expect(glance.editImageProps).toHaveBeenCalledWith('1', 'updated', ['removed']);
    });

    it('should edit volume metadata', function() {
      spyOn(cinder, 'editVolumeMetadata');
      metadataService.editMetadata('volume', '1', 'updated', ['removed']);
      expect(cinder.editVolumeMetadata).toHaveBeenCalledWith('1', 'updated', ['removed']);
    });

    it('should edit volume snapshot metadata', function() {
      spyOn(cinder, 'editVolumeSnapshotMetadata');
      metadataService.editMetadata('volume_snapshot', '1', 'updated', ['removed']);
      expect(cinder.editVolumeSnapshotMetadata).toHaveBeenCalledWith('1', 'updated', ['removed']);
    });

    it('should get image namespace', function() {
      spyOn(glance, 'getNamespaces');
      metadataService.getNamespaces('image');
      expect(glance.getNamespaces)
      .toHaveBeenCalledWith({ resource_type: 'OS::Glance::Image' }, false);
    });

    it('should get instance metadata', function() {
      var expected = 'instance metadata';
      spyOn(nova, 'getInstanceMetadata').and.returnValue(expected);
      var actual = metadataService.getMetadata('instance', '1');
      expect(actual).toBe(expected);
    });

    it('should get volume metadata', function() {
      var expected = 'volume metadata';
      spyOn(cinder, 'getVolumeMetadata').and.returnValue(expected);
      var actual = metadataService.getMetadata('volume', '1');
      expect(actual).toBe(expected);
    });

    it('should edit instance metadata', function() {
      spyOn(nova, 'editInstanceMetadata');
      metadataService.editMetadata('instance', '1', 'updated', ['removed']);
      expect(nova.editInstanceMetadata).toHaveBeenCalledWith('1', 'updated', ['removed']);
    });

    it('should get instance namespace', function() {
      spyOn(glance, 'getNamespaces');
      metadataService.getNamespaces('instance', 'metadata');
      expect(glance.getNamespaces)
      .toHaveBeenCalledWith({ resource_type: 'OS::Nova::Server',
                              properties_target: 'metadata' }, false);
    });

  });

})();
