/**
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

(function() {
  'use strict';

  describe('horizon.app.tech-debt.ImageFormController', function() {

    var $document, controller;
    var gzHtml = '<div id="id_disk_format"><input class="disk_format" value="gz"></input></div>';

    beforeEach(module('horizon.app.tech-debt'));
    beforeEach(inject(function($injector) {
      controller = $injector.get('$controller');
      $document = $injector.get('$document');
    }));

    function createController() {
      return controller('ImageFormController', {});
    }

    it('should set copyFrom', function() {
      $document.find('body').append('<input class="image_url" value="ImageUrl"></input>');

      var ctrl = createController();
      expect(ctrl.copyFrom).toEqual('ImageUrl');
      $document.find('.image_url').remove();
    });

    it('should set diskFormat', function() {
      $document.find('body').append('<input class="disk_format" value="DiskFormat"></input>');

      var ctrl = createController();
      expect(ctrl.diskFormat).toEqual('DiskFormat');
      $document.find('.disk_format').remove();
    });

    it('should set image format to detected format', function() {
      $document.find('body').append(gzHtml);

      var ctrl = createController();

      ctrl.selectImageFormat("image.tar.gz");

      expect(ctrl.diskFormat).toEqual('gz');
      $document.find('#id_disk_format').remove();
    });

    it('should set disk format to blank if selection does not match', function() {
      $document.find('body').append(gzHtml);

      var ctrl = createController();

      ctrl.selectImageFormat("image.tar.bz2");

      expect(ctrl.diskFormat).toEqual('');
      $document.find('#id_disk_format').remove();
    });

    it('should not set disk format to blank if path is empty', function() {
      $document.find('body').append(gzHtml);

      var ctrl = createController();

      ctrl.selectImageFormat();

      expect(ctrl.diskFormat).toEqual('gz');
      $document.find('#id_disk_format').remove();
    });

  });
})();
