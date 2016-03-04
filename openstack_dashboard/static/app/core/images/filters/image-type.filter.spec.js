/**
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

  describe('horizon.app.core.images.imageType Filter', function () {
    beforeEach(module('horizon.framework.util.i18n'));
    beforeEach(module('horizon.app.core.images'));

    describe('imageType', function () {
      var imageTypeFilter;
      beforeEach(inject(function (_imageTypeFilter_) {
        imageTypeFilter = _imageTypeFilter_;
      }));

      it('returns Snapshot for snapshot', function () {
        expect(imageTypeFilter({properties:{image_type:'snapshot'}})).toBe('Snapshot');
      });

      it('returns Image for image', function () {
        expect(imageTypeFilter({properties:{image_type:'image'}})).toBe('Image');
      });

      it('returns Image for null', function () {
        expect(imageTypeFilter(null)).toBe('Image');
      });

      it('returns Image for undefined', function () {
        expect(imageTypeFilter()).toBe('Image');
      });

    });

  });
})();
