// Add/remove table columns?
(function($, window, document, undefined) {
  $.fn.columnar = function (target, opt) {
    var options = $.extend({
      trigger: 'change',
      retrieve: 'name',
      container: $('table.sortable'),
      selector: '.',
      selected_class: 'hidden'
    }, opt);

    $(this).bind(options.trigger, function(e) {
      options.container.find( options.selector + $(this).attr(options.retrieve) ).toggleClass(options.selected_class)
    });
  };
} (jQuery, this, document));
