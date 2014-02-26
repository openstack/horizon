/*global angular*/
(function () {
  'use strict';
  angular.module('hz.conf', [])
    .constant('hzConfig', {
      // Placeholders; updated by Django.
      debug: null,  //
      static_url: null,
      ajax: {
        queue_limit: null
      },

      // Config options which may be overridden.
      spinner_options: {
        inline: {
          lines:  10,
          length: 5,
          width:  2,
          radius: 3,
          color:  '#000',
          speed:  0.8,
          trail:  50,
          zIndex: 100
        },
        modal: {
          lines:  10,
          length: 15,
          width:  4,
          radius: 10,
          color:  '#000',
          speed:  0.8,
          trail:  50
        },
        line_chart: {
          lines:  10,
          length: 15,
          width:  4,
          radius: 11,
          color:  '#000',
          speed:  0.8,
          trail:  50
        }
      }
    });
}());
