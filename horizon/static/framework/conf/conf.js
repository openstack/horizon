(function () {
  'use strict';

  angular
    .module('horizon.framework.conf', [])
    .constant('horizon.framework.conf.spinner_options', {
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
    })
    .value('horizon.framework.conf.toastOptions', {
      'delay': 3000,
      'dimissible': ['alert-success', 'alert-info']
    });
})();
