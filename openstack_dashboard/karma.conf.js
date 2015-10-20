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
  var xstaticPath;
  var basePaths = [
    './.venv',
    './.tox/py27'
  ];

  for (var i = 0; i < basePaths.length; i++) {
    var basePath = path.resolve(basePaths[i]);

    if (fs.existsSync(basePath)) {
      xstaticPath = basePath + '/lib/python2.7/site-packages/xstatic/pkg/';
      break;
    }
  }

  if (!xstaticPath) {
    console.error('xStatic libraries not found, please set up venv');
    process.exit(1);
  }

  config.set({
    preprocessors: {
      // Used to collect templates for preprocessing.
      // NOTE: the templates must also be listed in the files section below.
      './**/*.html': ['ng-html2js'],
      // Used to indicate files requiring coverage reports.
      './static/app/**/!(*.spec).js': ['coverage'],
      './dashboards/**/static/**/!(*.spec).js': ['coverage']
    },

    // Sets up module to process templates.
    ngHtml2JsPreprocessor: {
      moduleName: 'templates',
      cacheIdFromPath: function(filepath) {
        // This function takes the raw provided path from the file searches
        // below (in the files: pattern list), applies the filter from the
        // preprocessor above (basically, finds the html files), then uses
        // this function to translate the relative file path into a path
        // that matches what would actually be called in production.
        //
        // e.g.
        // dashboards/project/static/dashboard/project/workflow/launch-instance/configuration/load-edit.html
        // becomes:
        // /static/dashboard/project/workflow/launch-instance/configuration/load-edit.html
        // We can't just use stripPrefix because there are a couple of
        // prefixes that need to be altered (and may be more).
        return filepath.replace(/^dashboards\/[^\/]+/, '')
          .replace(/^static\/app/, '/static/app');
      },
    },

    // This establishes the base for most referenced paths as being relative
    // to this file, i.e. ./openstack_dashboard.
    basePath: './',

    // Contains both source and test files.
    files: [
      /*
       * shim, partly stolen from /i18n/js/horizon/
       * Contains expected items not provided elsewhere (dynamically by
       * Django or via jasmine template.  This is in the project root.
       */
      '../test-shim.js',

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
      xstaticPath + 'spin/data/spin.js',
      xstaticPath + 'spin/data/spin.jquery.js',

      // TODO: These should be mocked.  However, that could be complex
      // and there's less harm in exposing these directly.  These are
      // located in the project's ./horizon directory.
      '../horizon/static/horizon/js/horizon.js',

      /**
       * Include framework source code from horizon that we need.
       * Otherwise, karma will not be able to find them when testing.
       * These files should be mocked in the foreseeable future.
       * These are located within the project's ./horizon directory.
       */
      '../horizon/static/framework/**/*.module.js',
      '../horizon/static/framework/**/!(*.spec|*.mock).js',

      /**
       * Standard openstack_dashboard JS locations
       *
       * For now, all Angular code is located in ./static/app or
       * ./dashboard/.../static/.
       *
       * Some other JS code exists in other directories (contrib, test) but
       * but it isn't conformant to our current practices, etc.
       */

      /**
       * First, list all the files that defines application's angular modules.
       * Those files have extension of `.module.js`. The order among them is
       * not significant.
       */
      './static/app/**/*.module.js',
      './dashboards/**/static/**/*.module.js',

      /**
       * Followed by other JavaScript files that defines angular providers
       * on the modules defined in files listed above. And they are not mock
       * files or spec files defined below. The order among them is not
       * significant.
       */
      './static/app/**/!(*.spec|*.mock).js',
      './dashboards/**/static/**/!(*.spec|*.mock).js',

      /**
       * Then, list files for mocks with `mock.js` extension. The order
       * among them should not be significant.
       */
      './static/app/**/*.mock.js',
      './dashboards/**/static/**/*.mock.js',

      /**
       * Finally, list files for spec with `spec.js` extension. The order
       * among them should not be significant.
       */
      './static/app/**/*.spec.js',
      './dashboards/**/static/**/*.spec.js',

      /**
       * Angular external templates
       */
      './static/app/**/*.html',
      './dashboards/**/static/**/*.html'
    ],

    autoWatch: true,

    frameworks: ['jasmine'],

    browsers: ['PhantomJS'],

    phantomjsLauncher: {
      // Have phantomjs exit if a ResourceError is encountered
      // (useful if karma exits without killing phantom)
      exitOnResourceError: true
    },

    reporters: ['progress', 'coverage', 'threshold'],

    plugins: [
      'karma-phantomjs-launcher',
      'karma-jasmine',
      'karma-ng-html2js-preprocessor',
      'karma-coverage',
      'karma-threshold-reporter'
    ],

    // Places coverage report in HTML format in the subdirectory below.
    coverageReporter: {
      type: 'html',
      dir: './coverage-karma/'
    },

    // Coverage threshold values.
    thresholdReporter: {
      statements: 95, // target 100
      branches: 92, // target 100
      functions: 94, // target 100
      lines: 95 // target 100
    }
  });
};
