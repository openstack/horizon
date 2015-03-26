module.exports = function(config){

  // Path to xstatic pkg path.
  var xstaticPath = '../../.venv/lib/python2.7/site-packages/xstatic/pkg/';

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
      'horizon/js/angular/hz.api.module.js',
      'horizon/js/angular/services/**/*.js',
      'horizon/js/angular/hz.api.module.js',
      'dashboard-app/dashboard-app.module.js',
      'dashboard-app/utils/utils.module.js',
      'dashboard-app/**/*.js',
      'framework/framework.module.js',
      'framework/widgets/charts/charts.js',
      'framework/widgets/metadata-tree/metadata-tree.js',
      'framework/widgets/table/table.js',

      // Catch-all for stuff that isn't required explicitly by others.
      'framework/**/!(*spec).js',

      // Templates.
      './**/*.html',

      // TESTS
      '**/*.spec.js',
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

