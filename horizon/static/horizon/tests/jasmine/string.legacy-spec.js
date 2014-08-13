/*
 * Copyright 2015 IBM Corp.
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
describe("String utilities (horizon.string.js)", function() {

  describe("Escape Regex", function() {
    var escapeRegex = horizon.string.escapeRegex;
    var noRegexChars = 'string with no regex chars';
    var mixed = '\'$24.00 ^ ?"';
    var allRegexChars = '.*+?^${}()[]|/\\';

    it('should escape regular expression characters', function () {
      expect(escapeRegex(noRegexChars)).toBe(noRegexChars);
      expect(escapeRegex(mixed)).toBe('\'\\$24\\.00 \\^ \\?"');
      expect(escapeRegex(allRegexChars)).toBe('\\.\\*\\+\\?\\^\\$\\{\\}\\(\\)\\[\\]\\|\\/\\\\');
    });
  });

  describe("Escape HTML", function() {
    var escapeHtml = horizon.string.escapeHtml;
    var noHtmlChars = 'string with no HTML chars';
    var mixed = 'foo & <b>bar</b>';
    var allHtmlChars = '&<>"\'/';

    it('should escape HTML characters', function () {
      expect(escapeHtml(noHtmlChars)).toBe(noHtmlChars);
      expect(escapeHtml(mixed)).toBe('foo &amp; &lt;b&gt;bar&lt;&#x2F;b&gt;');
      expect(escapeHtml(allHtmlChars)).toBe('&amp;&lt;&gt;&quot;&#x27;&#x2F;');
    });
  });
});
