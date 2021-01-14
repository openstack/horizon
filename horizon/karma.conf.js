/*
 *    (c) Copyright 2015 Hewlett-Packard Development Company, L.P.
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

'use strict';

var fs = require('fs');
var path = require('path');

module.exports = function (config) {
  var xstaticPath = path.resolve('./.tox/npm');

  if (!xstaticPath) {
    console.error('xStatic libraries not found, please run `tox -e npm`');
    process.exit(1);
  }
  xstaticPath += '/lib/';
  xstaticPath += fs.readdirSync(xstaticPath).find(function(directory) {
    return directory.indexOf('python') === 0;
  });
  xstaticPath += '/site-packages/xstatic/pkg/';

  config.set({
    preprocessors: {
      // Used to collect templates for preprocessing.
      // NOTE: the templates must also be listed in the files section below.
      './**/*.html': ['ng-html2js'],
      // Used to indicate files requiring coverage reports.
      './**/!(*.spec|*.borrowed-from-underscore).js': ['coverage']
    },

    // Sets up module to process templates.
    ngHtml2JsPreprocessor: {
      prependPrefix: '/static/',
      moduleName: 'templates'
    },

    // Assumes you're in the top-level horizon directory.
    basePath: './static/',

    // Contains both source and test files.
    files: [
      /*
       * shim, partly stolen from /i18n/js/horizon/
       * Contains expected items not provided elsewhere (dynamically by
       * Django or via jasmine template.
       */
      '../../test-shim.js',

      // from jasmine.html
      xstaticPath + 'jquery/data/jquery.js',
      xstaticPath + 'angular/data/angular.js',
      xstaticPath + 'angular/data/angular-route.js',
      xstaticPath + 'angular/data/angular-mocks.js',
      xstaticPath + 'angular/data/angular-cookies.js',
      xstaticPath + 'angular_bootstrap/data/angular-bootstrap.js',
      xstaticPath + 'angular_gettext/data/angular-gettext.js',
      xstaticPath + 'angular/data/angular-sanitize.js',
      xstaticPath + 'd3/data/d3.js',
      xstaticPath + 'rickshaw/data/rickshaw.js',
      xstaticPath + 'angular_smart_table/data/smart-table.js',
      xstaticPath + 'angular_lrdragndrop/data/lrdragndrop.js',
      xstaticPath + 'angular_fileupload/data/ng-file-upload-all.js',
      xstaticPath + 'spin/data/spin.js',
      xstaticPath + 'spin/data/spin.jquery.js',
      xstaticPath + 'tv4/data/tv4.js',
      xstaticPath + 'objectpath/data/ObjectPath.js',
      xstaticPath + 'angular_schema_form/data/schema-form.js',

      // from jasmine_tests.py; only those that are deps for others
      'horizon/js/horizon.js',
      'horizon/js/horizon.uuid.js',

      /**
       * First, list all the files that defines application's angular modules.
       * Those files have extension of `.module.js`. The order among them is
       * not significant.
       */
      '**/*.module.js',

      /**
       * Followed by other JavaScript files that defines angular providers
       * on the modules defined in files listed above. And they are not mock
       * files or spec files defined below. The order among them is not
       * significant.
       */
      '!(horizon)/**/!(*.spec|*.mock).js',

      /**
       * Then, list files for mocks with `mock.js` extension. The order
       * among them should not be significant.
       */
      '**/*.mock.js',

      /**
       * Finally, list files for spec with `spec.js` extension. The order
       * among them should not be significant.
       */
      '**/*.spec.js',

      /**
       * Angular external templates
       */
      '**/*.html'
    ],

    autoWatch: true,

    frameworks: ['jasmine'],

    browsers: ['Firefox'],

    browserNoActivityTimeout: 60000,

    reporters: ['progress', 'coverage', 'threshold'],

    plugins: [
      'karma-firefox-launcher',
      'karma-jasmine',
      'karma-ng-html2js-preprocessor',
      'karma-coverage',
      'karma-threshold-reporter'
    ],

    coverageReporter: {
      type: 'html',
      dir: '../../cover/horizon'
    },

    client: {
      jasmine: {
        random: false
      }
    },

    // Coverage threshold values.
    thresholdReporter: {
      statements: 92, // target 100
      branches: 84, // target 100
      functions: 91, // target 100
      lines: 92 // target 100
    }
  });
};
