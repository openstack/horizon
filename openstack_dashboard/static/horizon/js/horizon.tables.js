/* Namespace for core functionality related to DataTables. */
horizon.datatables = {

};

horizon.datatables.update_footer_count = function (el, modifier) {
  var $el = $(el),
    $browser, $footer, row_count, footer_text_template, footer_text;
  if (!modifier) {
    modifier = 0;
  }
  // code paths for table or browser footers...
  $browser = $el.closest("#browser_wrapper");
  if ($browser.length) {
    $footer = $browser.find('.tfoot span.content_table_count');
  }
  else {
    $footer = $el.find('tfoot span.table_count');
  }
  row_count = $el.find('tbody tr:visible').length + modifier - $el.find('.empty').length;
  footer_text_template = ngettext("Displaying %s item", "Displaying %s items", row_count);
  footer_text = interpolate(footer_text_template, [row_count]);
  $footer.text(footer_text);
  return row_count;
};

horizon.datatables.add_no_results_row = function (table) {
  // Add a "no results" row if there are no results.
  template = horizon.templates.compiled_templates["#empty_row_template"];
  if (!table.find("div.list-group-item:visible").length 
      && typeof(template) !== "undefined") {
    table.append(template.render());
  }
};

horizon.datatables.remove_no_results_row = function (table) {
  table.find("p.empty").remove();
};



horizon.datatables.set_table_query_filter = function (parent) {
  horizon.datatables.qs = {};
  $(parent).find('div.panel').each(function (index, elm) {
    var input = $($(elm).find('div.table_search.client input')),
        table_selector;
    if (input.length > 0) {
      // Disable server-side searching if we have client-side searching since
      // (for now) the client-side is actually superior. Server-side filtering
      // remains as a noscript fallback.
      // TODO(gabriel): figure out an overall strategy for making server-side
      // filtering the preferred functional method.
      input.on('keypress', function (evt) {
        if (evt.keyCode === 13) {
          return false;
        }
      });
      input.next('button.btn span.fa-search').on('click keypress', function (evt) {
        return false;
      });

      // Enable the client-side searching.
      table_selector = '#' + $(elm).find('div.list-group').attr('id');
      var qs = input.quicksearch(table_selector + ' div.list-group-item', {
        'delay': 300,
        'loader': 'span.loading',
        'bind': 'keyup click',
        'show': this.show,
        'hide': this.hide,
        onBefore: function () {
          var table = $(table_selector);
          horizon.datatables.remove_no_results_row(table);
        },
        onAfter: function () {
          var template, table, colspan, params;
          table = $(table_selector);
          //horizon.datatables.update_footer_count(table);
          horizon.datatables.add_no_results_row(table);
        },
        prepareQuery: function (val) {
          return new RegExp(val, "i");
        },
        testQuery: function (query, txt, _row) {
          return query.test($(_row).find('div.name:not(.hidden):not(.actions_column)').text());
        }
      });
      //horizon.datatables.qs[$(elm).attr('id')] = qs;
    }
  });
};


horizon.addInitFunction(function() {
  //horizon.datatables.validate_button();
  $('table.datatable').each(function (idx, el) {
    horizon.datatables.update_footer_count($(el), 0);
  });

  // Trigger run-once setup scripts for tables.
  horizon.datatables.set_table_query_filter($('body'));

  // Also apply on tables in modal views.
  horizon.modals.addModalInitFunction(horizon.datatables.set_table_query_filter);

  // Also apply on tables in tabs views for lazy-loaded data.
  horizon.tabs.addTabLoadFunction(horizon.datatables.set_table_query_filter);
  //horizon.tabs.addTabLoadFunction(horizon.datatables.validate_button);

  //horizon.datatables.update();
});
