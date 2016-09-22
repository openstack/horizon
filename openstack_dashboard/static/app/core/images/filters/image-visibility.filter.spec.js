/**
 * (c) Copyright 2016 Hewlett-Packard Development Company, L.P.
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

  describe('horizon.app.core.images Filter', function () {
    beforeEach(module('horizon.framework'));
    beforeEach(module('horizon.app.core.images'));

    describe('imageVisibility', function () {
      var imageVisibilityFilter;
      beforeEach(inject(function (_imageVisibilityFilter_) {
        imageVisibilityFilter = _imageVisibilityFilter_;
      }));

      var expected = {
        public: 'Public',
        private: 'Private',
        other: "Image from Other Project - Non-Public",
        unknown: 'Unknown'
      };

      // Visibility (v2) attribute testing

      it('returns Public for visibility.public', function () {
        expect(imageVisibilityFilter({visibility: 'public'})).toBe(expected.public);
      });

      it('returns Private for visibility.private', function () {
        expect(imageVisibilityFilter({visibility: 'private'})).toBe(expected.private);
      });

      // Sharing is derived. If the current project can see a non-public image, but the image
      // is not "owned" by the current project, then it is shared with the project.

      it('returns Shared for visibility.private and owner is not current project', function () {
        expect(imageVisibilityFilter({visibility: 'private', owner: 'me'}, 'not me'))
          .toBe(expected.other);
      });

      it('returns Private for visibility.private and owner undefined', function () {
        expect(imageVisibilityFilter({visibility: 'private'})).toBe(expected.private);
      });

      it('returns Public for visibility.public and owner is current project', function () {
        expect(imageVisibilityFilter({visibility: 'public', owner: 'me'}, 'me'))
          .toBe(expected.public);
      });

      it('returns Public for visibility.public and owner is not current project', function () {
        expect(imageVisibilityFilter({visibility: 'public', owner: 'me'}, 'not me'))
          .toBe(expected.public);
      });

      it('returns Private for visibility.private and owner is current project', function () {
        expect(imageVisibilityFilter({visibility: 'private', owner: 'me'}), 'me')
          .toBe(expected.private);
      });

      // If we don't know this visibility, just return it back because we don't know
      // how to map it properly
      it('returns foo_bar for foo_bar visibility', function () {
        expect(imageVisibilityFilter({visibility: 'foo_bar'})).toBe('foo_bar');
      });

      //Prefer visibility (v2) over is_public (v1).
      it('returns visibility value when both visibilty and is_public set', function () {
        expect(imageVisibilityFilter({visibility: 'private', is_public: true}))
          .toBe(expected.private);
      });

      // is_public (v1) attribute testing

      it('returns Public for is_public = true', function () {
        expect(imageVisibilityFilter({is_public: true})).toBe(expected.public);
      });

      // Sharing is derived. If the current project can see a non-public image, but the image
      // is not "owned" by the current project, then it is shared with project.

      it('returns Shared for is_public = false and owner is not current project', function () {
        expect(imageVisibilityFilter({is_public: false, owner: 'me'}, 'not me'))
          .toBe(expected.other);
      });

      it('returns Private for is_public = false and owner undefined', function () {
        expect(imageVisibilityFilter({is_public: false})).toBe(expected.private);
      });

      it('returns Public for is_public = true and owner is current project', function () {
        expect(imageVisibilityFilter({is_public: true, owner: 'me'}, 'me'))
          .toBe(expected.public);
      });

      it('returns Public for is_public = true and owner is not current project', function () {
        expect(imageVisibilityFilter({is_public: true, owner: 'me'}, 'not me'))
          .toBe(expected.public);
      });

      it('returns Private for is_public = false and owner is current project', function () {
        expect(imageVisibilityFilter({is_public: false, owner: 'me'}), 'me')
          .toBe(expected.private);
      });

      // Bad input still gives a translated status of unknown

      it('returns Unknown for is_public = undefined', function () {
        expect(imageVisibilityFilter({})).toBe(expected.unknown);
      });

      it('returns Unknown for null', function () {
        expect(imageVisibilityFilter(null)).toBe(expected.unknown);
      });

      it('returns Unknown for undefined input', function () {
        expect(imageVisibilityFilter()).toBe(expected.unknown);
      });

    });

  });
})();
