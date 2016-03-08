/* Namespace for core functionality related to DataTables. */
horizon.datatables = {
  update: function () {
    var $rows_to_update = $('tr.status_unknown.ajax-update'),
      rows_to_update = $rows_to_update.length;
    if ( rows_to_update > 0 ) {
      var interval = $rows_to_update.attr('data-update-interval'),
        $table = $rows_to_update.closest('table'),
        submit_in_progress = $table.closest('form').attr('data-submitted'),
        decay_constant = $table.attr('decay_constant');

      // Do not update this row if the action column is expanded or the form
      // is in the process of being submitted. If we update the row while the
      // form is still submitting any disabled action buttons would potentially
      // be enabled again, allowing for multiple form submits.
      if ($rows_to_update.find('.actions_column .btn-group.open').length ||
          submit_in_progress) {
        // Wait and try to update again in next interval instead
        setTimeout(horizon.datatables.update, interval);
        // Remove interval decay, since this will not hit server
        $table.removeAttr('decay_constant');
        return;
      }
      // Trigger the update handlers.
      $rows_to_update.each(function() {
        var $row = $(this),
          $table = $row.closest('table.datatable');
        horizon.ajax.queue({
          url: $row.attr('data-update-url'),
          error: function (jqXHR) {
            switch (jqXHR.status) {
              // A 404 indicates the object is gone, and should be removed from the table
              case 404:
                // Update the footer count and reset to default empty row if needed
                var row_count, colspan, template, params;

                // existing count minus one for the row we're removing
                row_count = horizon.datatables.update_footer_count($table, -1);

                if(row_count === 0) {
                  colspan = $table.find('.table_column_header th').length;
                  template = horizon.templates.compiled_templates["#empty_row_template"];
                  params = {
                      "colspan": colspan,
                      no_items_label: gettext("No items to display.")
                  };
                  var empty_row = template.render(params);
                  $row.replaceWith(empty_row);
                } else {
                  $row.remove();
                }
                // Reset tablesorter's data cache.
                $table.trigger("update");
                // Enable launch action if quota is not exceeded
                horizon.datatables.update_actions();
                break;
              default:
                console.log(gettext("An error occurred while updating."));
                $row.removeClass("ajax-update");
                $row.find("i.ajax-updating").remove();
                break;
            }
          },
          success: function (data) {
            var $new_row = $(data);

            if ($new_row.hasClass('status_unknown')) {
              var $container = $(document.createElement('div'))
                .addClass('horizon-pending-bar');

              var $progress = $(document.createElement('div'))
                .addClass('progress progress-striped active')
                .appendTo($container);

              $(document.createElement('div'))
                .addClass('progress-bar')
                .css("width", "100%")
                .appendTo($progress);

              // if action/confirm is required, show progress-bar with "?"
              // icon to indicate user action is required
              if ($new_row.find('.btn-action-required').length > 0) {
                $(document.createElement('span'))
                  .addClass('fa fa-question-circle horizon-pending-bar-icon')
                  .appendTo($container);
              }
              $new_row.find("td.status_unknown:last").prepend($container);
            }

            // Only replace row if the html content has changed
            if($new_row.html() !== $row.html()) {

              // Directly accessing the checked property of the element
              // is MUCH faster than using jQuery's helper method
              var $checkbox = $row.find('.table-row-multi-select');
              if($checkbox.length && $checkbox[0].checked) {
                // Preserve the checkbox if it's already clicked
                $new_row.find('.table-row-multi-select').prop('checked', true);
              }
              $row.replaceWith($new_row);

              // TODO(matt-borland, tsufiev): ideally we should solve the
              // problem with not-working angular actions in a content added
              // by jQuery via replacing jQuery insert with Angular insert.
              // Should address this in Newton release
              recompileAngularContent();

              // Reset tablesorter's data cache.
              $table.trigger("update");
              // Reset decay constant.
              $table.removeAttr('decay_constant');
              // Check that quicksearch is enabled for this table
              // Reset quicksearch's data cache.
              if ($table.attr('id') in horizon.datatables.qs) {
                horizon.datatables.qs[$table.attr('id')].cache();
              }
            }
          },
          complete: function () {
            // Revalidate the button check for the updated table
            horizon.datatables.validate_button();
            rows_to_update--;
            // Schedule next poll when all the rows are updated
            if ( rows_to_update === 0 ) {
              // Set interval decay to this table, and increase if it already exist
              if(decay_constant === undefined) {
                decay_constant = 1;
              } else {
                decay_constant++;
              }
              $table.attr('decay_constant', decay_constant);
              // Poll until there are no rows in an "unknown" state on the page.
              var next_poll = interval * decay_constant;
              // Limit the interval to 30 secs
              if(next_poll > 30 * 1000) { next_poll = 30 * 1000; }
              setTimeout(horizon.datatables.update, next_poll);
            }
          }
        });
      });
    }
  },

  update_actions: function() {
    var $actions_to_update = $('.btn-launch.ajax-update, .btn-create.ajax-update');
    $actions_to_update.each(function() {
      var $action = $(this);
      horizon.ajax.queue({
        url: $action.attr('data-update-url'),
        error: function () {
          console.log(gettext("An error occurred while updating."));
        },
        success: function (data) {
          var $new_action = $(data);

          // Only replace row if the html content has changed
          if($new_action.html() != $action.html()) {
            $action.replaceWith($new_action);
          }
        }
      });
    });
  },

  validate_button: function ($form, disable_button) {
    // Enable or disable table batch action buttons based on row selection.
    $form = $form || $(".table_wrapper > form");
    $form.each(function () {
      var $this = $(this);
      var $action_buttons = $this.find('.table_actions button[data-batch-action="true"]');
      if (typeof disable_button == undefined) {
        disable_button = $this.find(".table-row-multi-select").filter(":checked").length > 0;
      }
      $action_buttons.toggleClass("disabled", disable_button);
    });
  },

  initialize_checkboxes_behavior: function() {
    // Bind the "select all" checkbox action.
    $('.table_wrapper, #modal_wrapper')
      .on('change', '.table-row-multi-select', function() {
        var $this = $(this);
        var $table = $this.closest('table');
        var is_checked = $this.prop('checked');

        if ($this.hasClass('multi-select-header')) {

          // Only select / deselect the visible rows
          $table.find('tbody tr:visible .table-row-multi-select')
            .prop('checked', is_checked);

        } else {

          // Find the master checkbox
          var $multi_select_checkbox = $table.find('.multi-select-header');

          // Determine if there are any unchecked checkboxes in the table
          var $checkboxes = $table.find('tbody .table-row-multi-select');
          var not_checked = $checkboxes.not(':checked').length;
          is_checked = $checkboxes.length != not_checked;

          // If there are none, then check the master checkbox
          $multi_select_checkbox.prop('checked', not_checked == 0);
        }

        // Pass in whether it should be visible, no point in doing this twice
        horizon.datatables.validate_button($this.closest('form'), !is_checked);
      });
  },

  initialize_table_tooltips: function() {
    $('div.table_wrapper').tooltip({selector: '[data-toggle="tooltip"]', container: 'body'});
  },

  disable_actions_on_submit: function($form) {
    // This applies changes to the table form when a user takes an action that
    // submits the form. It relies on the form being re-rendered after the
    // submit is completed to remove these changes.
    $form = $form || $(".table_wrapper > form");
    $form.on("submit", function () {
      var $this = $(this);
      // Add the 'submitted' flag to the form so the row update interval knows
      // not to update the row and therefore re-enable the actions that we are
      // disabling here.
      $this.attr('data-submitted', 'true');
      // Disable row action buttons. This prevents multiple form submission.
      $this.find('td.actions_column button[type="submit"]').addClass("disabled");
      // Use CSS to update the cursor so it's very clear that an action is
      // in progress.
      $this.addClass('wait');
    });
  }
};

/* Generates a confirmation modal dialog for the given action. */
horizon.datatables.confirm = function (action) {
  var $action = $(action),
    $modal_parent = $(action).closest('.modal'),
    name_array = [],
    closest_table_id, action_string, name_string,
    help_text,
    title, body, modal, form;
  if($action.hasClass("disabled")) {
    return;
  }
  action_string = $action.text();
  help_text = $action.attr("help_text") || "";
  name_string = "";
  // Add the display name defined by table.get_object_display(datum)
  closest_table_id = $(action).closest("table").attr("id");
  // Check if data-display attribute is available
  if ($("#"+closest_table_id+" tr[data-display]").length > 0) {
    var actions_div = $(action).closest("div");
    if(actions_div.hasClass("table_actions") || actions_div.hasClass("table_actions_menu")) {
      // One or more checkboxes selected
      $("#"+closest_table_id+" tr[data-display]").has(".table-row-multi-select:checked").each(function() {
        name_array.push(" \"" + $(this).attr("data-display") + "\"");
      });
      name_array.join(", ");
      name_string = name_array.toString();
    } else {
      // If no checkbox is selected
      name_string = " \"" + $(action).closest("tr").attr("data-display") + "\"";
    }
    name_string = interpolate(gettext("You have selected %s. "), [name_string]);
  }
  title = interpolate(gettext("Confirm %s"), [action_string]);
  body = name_string + gettext("Please confirm your selection. ") + help_text;
  modal = horizon.modals.create(title, body, action_string);
  modal.modal();
  if($modal_parent.length) {
    var child_backdrop = modal.next('.modal-backdrop');
    // re-arrange z-index for these stacking modal
    child_backdrop.css('z-index', $modal_parent.css('z-index')+10);
    modal.css('z-index', child_backdrop.css('z-index')+10);
  }
  modal.find('.btn-primary').click(function () {
    form = $action.closest('form');
    var el = document.createElement("input");
    el.type='hidden';
    el.name = $action.attr('name');
    el.value = $action.attr('value');
    form.append(el);
    form.submit();
    modal.modal('hide');
    horizon.modals.modal_spinner(gettext("Working"));
    return false;
  });
  return modal;
};

$.tablesorter.addParser({
  // set a unique id
  id: 'sizeSorter',
  is: function() {
    // Not an auto-detected parser
    return false;
  },
  // compare int values
  format: function(s) {
    var sizes = {
      BYTE: 0,
      B: 0,
      KB: 1,
      MB: 2,
      GB: 3,
      TB: 4,
      PB: 5
    };
    var regex = /([\d\.,]+)\s*(byte|B|KB|MB|GB|TB|PB)+/i;
    var match = s.match(regex);
    if (match && match.length === 3){
      return parseFloat(match[1]) *
        Math.pow(1024, sizes[match[2].toUpperCase()]);
    }
    return parseInt(s, 10);
  },
  type: 'numeric'
});

$.tablesorter.addParser({
  // set a unique id
  id: 'timesinceSorter',
  is: function() {
    // Not an auto-detected parser
    return false;
  },
  // compare int values
  format: function(s, table, cell) {
    return $(cell).find('span').data('seconds');
  },
  type: 'numeric'
});

$.tablesorter.addParser({
  id: "timestampSorter",
  is: function() {
    return false;
  },
  format: function(s) {
    s = s.replace(/\-/g, " ").replace(/:/g, " ");
    s = s.replace("T", " ").replace("Z", " ");
    s = s.split(" ");
    return new Date(s[0], s[1], s[2], s[3], s[4], s[5]).getTime();
  },
  type: "numeric"
});

$.tablesorter.addParser({
  id: 'IPv4Address',
  is: function(s, table, cell) {
    // The first arg to this function is a string of all the cell's innertext smashed together
    // with no delimiters, so to make this work with the Instances and Ports tables where the
    // IP address cell content is an unordered list we need to check the content of the first
    // <li> element. In the Floating IPs and Subnets tables the cell content is not a list so
    // we just check the cell content directly.
    var a = $(cell).find('li').first().text().split('.');
    if (a.length === 1 && a[0] === '') {
      a = s.split('.');
    }
    if (a.length !== 4) {
      return false;
    }
    for (var i = 0; i < a.length; i++) {
      if (isNaN(a[i])) {
        return false;
      }
      if ((a[i] & 0xFF) != a[i]) {
        return false;
      }
    }
    return true;
  },
  format: function(s, table, cell) {
    var result = 0;
    var a = $(cell).find('li').first().text().split('.');
    if (a.length === 1 && a[0] === '') {
      a = s.split('.');
    }
    var last_index = a.length - 1;
    // inet_aton(3), Javascript-style.  The unsigned-right-shift operation is
    // needed to keep the result from flipping over to negative when suitably
    // large values are generated
    for (var i = 0; i < a.length; i++) {
      var shift = 8 * (last_index - i);
      result += ((parseInt(a[i], 10) << shift) >>> 0);
    }
    return result;
  },
  type: 'numeric'
});

horizon.datatables.disable_buttons = function() {
  $("table .table_actions").on("click", ".btn.disabled", function(event){
    event.preventDefault();
    event.stopPropagation();
  });
};

$.tablesorter.addParser({
  id: 'uuid',
  is: function() {
    return false;
  },
  format: function(s) {
    // Calculate a float that is based on the strings alphabetical position.
    //
    // Each character in the string has some significance in the
    // overall calculation, starting at 1.0 and is divided down by 2 decimal
    // places according to the chars position in the string.
    // For example the string "SO" would become 83.79 which is then
    // numerically comparable to other strings.
    s = s.toUpperCase();
    var value = 0.0;
    for(var i = 0; i < s.length; i++) {
      var char_offset = 1.0 / Math.pow(100, i);
      value = value + (s.charCodeAt(i) * char_offset);
    }
    return value;
  },
  type: 'numeric'
});

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
  if (row_count) {
    footer_text_template = ngettext("Displaying %s item", "Displaying %s items", row_count);
    footer_text = interpolate(footer_text_template, [row_count]);
  } else {
    footer_text = '';
  }
  $footer.text(footer_text);
  return row_count;
};

horizon.datatables.add_no_results_row = function (table) {
  // Add a "no results" row if there are no results.
  var template = horizon.templates.compiled_templates["#empty_row_template"];
  if (!table.find("tbody tr:visible").length && typeof(template) !== "undefined") {
    var colspan = $table.find('.table_column_header th').length;
    var params = {
        "colspan": colspan,
        no_items_label: gettext("No items to display.")
    };
    table.find("tbody").append(template.render(params));
  }
};

horizon.datatables.remove_no_results_row = function (table) {
  table.find("tr.empty").remove();
};

/*
 * Fixes the striping of the table after filtering results.
 **/
horizon.datatables.fix_row_striping = function (table) {
  table.trigger('applyWidgetId', ['zebra']);
};

horizon.datatables.set_table_sorting = function (parent) {
// Function to initialize the tablesorter plugin strictly on sortable columns.
  $(parent).find("table.datatable").each(function () {
    var $table = $(this),
      header_options = {};
    // Disable if not sortable or has <= 1 item
    if ($table.find('tbody tr').not('.empty').length > 1){
      $table.find("thead th[class!='table_header']").each(function (i) {
        var $th = $(this);
        if (!$th.hasClass('sortable')) {
          header_options[i] = {sorter: false};
        } else if ($th.data('type') === 'size'){
          header_options[i] = {sorter: 'sizeSorter'};
        } else if ($th.data('type') === 'ip'){
          header_options[i] = {sorter: 'IPv4Address'};
        } else if ($th.data('type') === 'timesince'){
          header_options[i] = {sorter: 'timesinceSorter'};
        } else if ($th.data('type') === 'timestamp'){
          header_options[i] = {sorter: 'timestampSorter'};
        } else if ($th.data('type') == 'uuid'){
          header_options[i] = {sorter: 'uuid'};
        }
      });
      $table.tablesorter({
        headers: header_options,
        widgets: ['zebra'],
        selectorHeaders: "thead th[class!='table_header']",
        cancelSelection: false,
        emptyTo: 'none'
      });
    }
  });
};

horizon.datatables.add_table_checkboxes = function($parent) {
  $($parent).find('table thead .multi_select_column').each(function() {
    var $thead = $(this);
    if (!$thead.find('.table-row-multi-select').length &&
      $thead.parents('table').find('tbody .table-row-multi-select').length) {

      // Build up the themable checkbox
      var $container = $(document.createElement('div'))
        .addClass('themable-checkbox');

      // Create the input checkbox
      var $input = $(document.createElement('input'))
        .attr('type', 'checkbox')
        .addClass('table-row-multi-select multi-select-header')
        .uniqueId()
        .appendTo($container);

      // Create the label
      $(document.createElement('label'))
        .attr('for', $input.attr('id'))
        .appendTo($container);

      // Append to the thead last, for speed
      $thead.append($container);
    }
  });
};

horizon.datatables.set_table_query_filter = function (parent) {
  horizon.datatables.qs = {};
  $(parent).find('table').each(function (index, elm) {
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
      input.next('button.btn span.search-icon').on('click keypress', function () {
        return false;
      });

      // Enable the client-side searching.
      table_selector = 'table#' + $(elm).attr('id');
      var qs = input.quicksearch(table_selector + ' tbody tr', {
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
          var table = $(table_selector);
          horizon.datatables.update_footer_count(table);
          horizon.datatables.add_no_results_row(table);
          horizon.datatables.fix_row_striping(table);
        },
        prepareQuery: function (val) {
          return new RegExp(horizon.string.escapeRegex(val), "i");
        },
        testQuery: function (query, txt, _row) {
          return query.test($(_row).find('td:not(.hidden):not(.actions_column)').text());
        }
      });
      horizon.datatables.qs[$(elm).attr('id')] = qs;
    }
  });
};

horizon.datatables.set_table_fixed_filter = function (parent) {
  $(parent).find('table.datatable').each(function (index, elm) {
    $(elm).on('click', 'div.table_filter button', function(evt) {
      // Remove active class from all buttons
      $(elm).find('div.table_filter button').each(function(index, btn) {
        $(btn).removeClass('active');
      });
      var table = $(elm);
      var category = $(this).val();
      evt.preventDefault();
      horizon.datatables.remove_no_results_row(table);
      table.find('tbody tr').hide();
      table.find('tbody tr.category-' + category).show();
      horizon.datatables.update_footer_count(table);
      horizon.datatables.add_no_results_row(table);
      horizon.datatables.fix_row_striping(table);
    });
    $(elm).find('div.table_filter button').each(function (i, button) {
      // Select the first non-empty category
      if ($(button).text().indexOf(' (0)') === -1) {
        $(button).trigger('click');
        return false;
      }
    });
  });
};

horizon.addInitFunction(horizon.datatables.init = function() {
  horizon.datatables.validate_button();
  horizon.datatables.disable_buttons();
  $('table.datatable').each(function (idx, el) {
    horizon.datatables.update_footer_count($(el), 0);
  });
  horizon.datatables.initialize_checkboxes_behavior();
  horizon.datatables.initialize_table_tooltips();

  // Trigger run-once setup scripts for tables.
  var $body = $('body');
  horizon.datatables.add_table_checkboxes($body);
  horizon.datatables.set_table_sorting($body);
  horizon.datatables.set_table_query_filter($body);
  horizon.datatables.set_table_fixed_filter($body);
  horizon.datatables.disable_actions_on_submit();

  // Also apply on tables in modal views.
  horizon.modals.addModalInitFunction(horizon.datatables.add_table_checkboxes);
  horizon.modals.addModalInitFunction(horizon.datatables.set_table_sorting);
  horizon.modals.addModalInitFunction(horizon.datatables.set_table_query_filter);
  horizon.modals.addModalInitFunction(horizon.datatables.set_table_fixed_filter);
  horizon.modals.addModalInitFunction(horizon.datatables.initialize_table_tooltips);
  horizon.modals.addModalInitFunction(function modalInitActionDisable(modal) {
    horizon.datatables.disable_actions_on_submit($(modal).find(".table_wrapper > form"));
  });

  // Also apply on tables in tabs views for lazy-loaded data.
  horizon.tabs.addTabLoadFunction(horizon.datatables.add_table_checkboxes);
  horizon.tabs.addTabLoadFunction(horizon.datatables.set_table_sorting);
  horizon.tabs.addTabLoadFunction(horizon.datatables.set_table_query_filter);
  horizon.tabs.addTabLoadFunction(horizon.datatables.set_table_fixed_filter);
  horizon.tabs.addTabLoadFunction(horizon.datatables.initialize_checkboxes_behavior);
  horizon.tabs.addTabLoadFunction(horizon.datatables.initialize_table_tooltips);
  horizon.tabs.addTabLoadFunction(function(tab) {
    horizon.datatables.validate_button($(tab).find(".table_wrapper > form"));
    horizon.datatables.disable_actions_on_submit($(tab).find(".table_wrapper > form"));
  });

  horizon.datatables.update();
});
