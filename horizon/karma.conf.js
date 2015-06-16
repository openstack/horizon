'use strict';
var fs = require('fs');
var path = require('path');

module.exports = function(config) {
  var xstaticPath;
  var basePaths = [
    './.venv',
    './.tox/py27'
  ]

  for (var i = 0; i < basePaths.length; i++) {
    var basePath = path.resolve(basePaths[i]);

    if (fs.existsSync(basePath)) {
      xstaticPath = basePath + '/lib/python2.7/site-packages/xstatic/pkg/';
      break;
    }
  }

  if (!xstaticPath) {
    console.error("xStatic libraries not found, please set up venv");
    process.exit(1);
  }

  config.set({

    preprocessors: {
      // Used to collect templates for preprocessing.
      // NOTE: the templates must also be listed in the files section below.
      './**/*.html': ['ng-html2js'],
      // Used to indicate files requiring coverage reports.
      './**/!(*spec).js': ['coverage']
    },

    // Sets up module to process templates.
    ngHtml2JsPreprocessor: {
      prependPrefix: '/static/',
      moduleName: 'templates'
    },

    // Assumes you're in the top-level horizon directory.
    basePath : './static/',

    // Contains both source and test files.
    files : [

      // shim, partly stolen from /i18n/js/horizon/
      // Contains expected items not provided elsewhere (dynamically by
      // Django or via jasmine template.
      '../../test-shim.js',

      // from jasmine.html
      xstaticPath + 'jquery/data/jquery.js',
      xstaticPath + 'angular/data/angular.js',
      xstaticPath + 'angular/data/angular-mocks.js',
      xstaticPath + 'angular/data/angular-cookies.js',
      xstaticPath + 'angular_bootstrap/data/angular-bootstrap.js',
      xstaticPath + 'angular/data/angular-sanitize.js',
      xstaticPath + 'd3/data/d3.js',
      xstaticPath + 'rickshaw/data/rickshaw.js',
      xstaticPath + 'angular_smart_table/data/smart-table.js',
      xstaticPath + 'angular_lrdragndrop/data/lrdragndrop.js',
      xstaticPath + 'spin/data/spin.js',
      xstaticPath + 'spin/data/spin.jquery.js',

      // from jasmine_tests.py; only those that are deps for others
      'horizon/js/horizon.js',
      '../../openstack_dashboard/static/openstack-service-api/openstack-service-api.module.js',
      'dashboard-app/dashboard-app.module.js',
      'dashboard-app/**/*.js',
      'auth/auth.module.js',
      'auth/login/login.module.js',
      'framework/framework.module.js',
      'framework/util/util.module.js',
      'framework/util/tech-debt/tech-debt.module.js',
      'framework/widgets/charts/charts.module.js',
      'framework/widgets/modal/modal.module.js',
      'framework/widgets/metadata-tree/metadata-tree.module.js',
      'framework/widgets/table/table.module.js',
      'framework/widgets/toast/toast.module.js',

      // Catch-all for stuff that isn't required explicitly by others.
      'auth/**/!(*spec).js',
      'framework/**/!(*spec).js',

      // Templates.
      './**/*.html',

      // Magic search requires late ordering due to overriding.
      xstaticPath + 'magic_search/data/magic_search.js',

      // TESTS
      '**/*.spec.js'
    ],

    autoWatch : true,

    frameworks: ['jasmine'],

    browsers : ['PhantomJS'],

    phantomjsLauncher: {
      // Have phantomjs exit if a ResourceError is encountered
      // (useful if karma exits without killing phantom)
      exitOnResourceError: true
    },

    reporters : [ 'progress', 'coverage' ],

    plugins : [
      'karma-phantomjs-launcher',
      'karma-jasmine',
      'karma-ng-html2js-preprocessor',
      'karma-coverage'
    ],

    coverageReporter: {
      type : 'html',
      dir : '../.coverage-karma/'
    }

  });
};

