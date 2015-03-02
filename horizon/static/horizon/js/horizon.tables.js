/* Namespace for core functionality related to DataTables. */
horizon.datatables = {
  update: function () {
    var $rows_to_update = $('tr.status_unknown.ajax-update');
    if ($rows_to_update.length) {
      var interval = $rows_to_update.attr('data-update-interval'),
        $table = $rows_to_update.closest('table'),
        decay_constant = $table.attr('decay_constant');

      // Do not update this row if the action column is expanded
      if ($rows_to_update.find('.actions_column .btn-group.open').length) {
        // Wait and try to update again in next interval instead
        setTimeout(horizon.datatables.update, interval);
        // Remove interval decay, since this will not hit server
        $table.removeAttr('decay_constant');
        return;
      }
      // Trigger the update handlers.
      $rows_to_update.each(function(index, row) {
        var $row = $(this),
          $table = $row.closest('table.datatable');
        horizon.ajax.queue({
          url: $row.attr('data-update-url'),
          error: function (jqXHR, textStatus, errorThrown) {
            switch (jqXHR.status) {
              // A 404 indicates the object is gone, and should be removed from the table
              case 404:
                // Update the footer count and reset to default empty row if needed
                var $footer, row_count, footer_text, colspan, template, params, $empty_row;

                // existing count minus one for the row we're removing
                row_count = horizon.datatables.update_footer_count($table, -1);

                if(row_count === 0) {
                  colspan = $table.find('th[colspan]').attr('colspan');
                  template = horizon.templates.compiled_templates["#empty_row_template"];
                  params = {
                      "colspan": colspan,
                      no_items_label: gettext("No items to display.")
                  };
                  empty_row = template.render(params);
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
                horizon.utils.log(gettext("An error occurred while updating."));
                $row.removeClass("ajax-update");
                $row.find("i.ajax-updating").remove();
                break;
            }
          },
          success: function (data, textStatus, jqXHR) {
            var $new_row = $(data);

            if ($new_row.hasClass('status_unknown')) {
              var spinner_elm = $new_row.find("td.status_unknown:last");
              var imagePath = $new_row.find('.btn-action-required').length > 0 ?
                "dashboard/img/action_required.png":
                "dashboard/img/loading.gif";
              imagePath = STATIC_URL + imagePath;
              spinner_elm.prepend(
                $("<div>")
                  .addClass("loading_gif")
                  .append($("<img>").attr("src", imagePath)));
            }

            // Only replace row if the html content has changed
            if($new_row.html() !== $row.html()) {
              if($row.find('.table-row-multi-select:checkbox').is(':checked')) {
                // Preserve the checkbox if it's already clicked
                $new_row.find('.table-row-multi-select:checkbox').prop('checked', true);
              }
              $row.replaceWith($new_row);
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
          complete: function (jqXHR, textStatus) {
            // Revalidate the button check for the updated table
            horizon.datatables.validate_button();

            // Set interval decay to this table, and increase if it already exist
            if(decay_constant === undefined) {
              decay_constant = 1;
            } else {
              decay_constant++;
            }
            $table.attr('decay_constant', decay_constant);
            // Poll until there are no rows in an "unknown" state on the page.
            next_poll = interval * decay_constant;
            // Limit the interval to 30 secs
            if(next_poll > 30 * 1000) { next_poll = 30 * 1000; }
            setTimeout(horizon.datatables.update, next_poll);
          }
        });
      });
    }
  },

  update_actions: function() {
    var $actions_to_update = $('.btn-launch.ajax-update, .btn-create.ajax-update');
    $actions_to_update.each(function(index, action) {
      var $action = $(this);
      horizon.ajax.queue({
        url: $action.attr('data-update-url'),
        error: function (jqXHR, textStatus, errorThrown) {
          horizon.utils.log(gettext("An error occurred while updating."));
        },
        success: function (data, textStatus, jqXHR) {
          var $new_action = $(data);

          // Only replace row if the html content has changed
          if($new_action.html() != $action.html()) {
            $action.replaceWith($new_action);
          }
        }
      });
    });
  },

  validate_button: function () {
    // Disable form button if checkbox are not checked
    $("form").each(function (i) {
      var checkboxes = $(this).find(".table-row-multi-select:checkbox");
      var action_buttons = $(this).find(".table_actions button.btn-danger");

      // Buttons should be enabled only if there are checked checkboxes
      if (checkboxes.length) {
        action_buttons.toggleClass("disabled",
          !checkboxes.filter(":checked").length);
        }
    });
  },

  initialize_checkboxes_behavior: function() {
    // Bind the "select all" checkbox action.
    $('div.table_wrapper, #modal_wrapper').on('click', 'table thead .multi_select_column .table-row-multi-select:checkbox', function(evt) {
      var $this = $(this),
      $table = $this.closest('table'),
      is_checked = $this.prop('checked'),
      checkboxes = $table.find('tbody .table-row-multi-select:visible:checkbox');
      checkboxes.prop('checked', is_checked);
    });
    // Change "select all" checkbox behavior while any checkbox is checked/unchecked.
    $("div.table_wrapper, #modal_wrapper").on("click", 'table tbody .table-row-multi-select:checkbox', function (evt) {
      var $table = $(this).closest('table');
      var $multi_select_checkbox = $table.find('thead .multi_select_column .table-row-multi-select:checkbox');
      var any_unchecked = $table.find("tbody .table-row-multi-select:checkbox").not(":checked");
      $multi_select_checkbox.prop('checked', any_unchecked.length === 0);
    });
    // Enable dangerous buttons only if one or more checkbox is checked.
    $("div.table_wrapper, #modal_wrapper").on("click", '.table-row-multi-select:checkbox', function (evt) {
      var $form = $(this).closest("form");
      var any_checked = $form.find("tbody .table-row-multi-select:checkbox").is(":checked");
      if(any_checked) {
        $form.find(".table_actions button.btn-danger").removeClass("disabled");
      }else {
        $form.find(".table_actions button.btn-danger").addClass("disabled");
      }
    });
  }

};

/* Generates a confirmation modal dialog for the given action. */
horizon.datatables.confirm = function (action) {
  var $action = $(action),
    $modal_parent = $(action).closest('.modal'),
    name_array = [],
    closest_table_id, action_string, name_string,
    title, body, modal, form;
  if($action.hasClass("disabled")) {
    return;
  }
  action_string = $action.text();
  name_string = "";
  // Add the display name defined by table.get_object_display(datum)
  closest_table_id = $(action).closest("table").attr("id");
  // Check if data-display attribute is available
  if ($("#"+closest_table_id+" tr[data-display]").length > 0) {
    var actions_div = $(action).closest("div");
    if(actions_div.hasClass("table_actions") || actions_div.hasClass("table_actions_menu")) {
      // One or more checkboxes selected
      $("#"+closest_table_id+" tr[data-display]").has(".table-row-multi-select:checkbox:checked").each(function() {
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
  body = name_string + gettext("Please confirm your selection. This action cannot be undone.");
  modal = horizon.modals.create(title, body, action_string);
  modal.modal();
  if($modal_parent.length) {
    var child_backdrop = modal.next('.modal-backdrop');
    // re-arrange z-index for these stacking modal
    child_backdrop.css('z-index', $modal_parent.css('z-index')+10);
    modal.css('z-index', child_backdrop.css('z-index')+10);
  }
  modal.find('.btn-primary').click(function (evt) {
    form = $action.closest('form');
    form.append("<input type='hidden' name='" + $action.attr('name') + "' value='" + $action.attr('value') + "'/>");
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
  is: function(s) {
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
  is: function(s) {
    // Not an auto-detected parser
    return false;
  },
  // compare int values
  format: function(s, table, cell, cellIndex) {
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
  id: 'naturalSort',
  is: function(s) {
    return false;
  },
  // compare int values, non-integers use the ordinal value of the first byte
  format: function(s) {
    result = parseInt(s);
    if (isNaN(result)) {
      m = s.match(/\d+/);
      if (m && m.length) {
        return parseInt(m[0]);
      } else {
        return s.charCodeAt(0);
      }
    } else {
      return result;
    }
  },
  type: 'numeric'
});

$.tablesorter.addParser({
  id: 'IPv4Address',
  is: function(s, table, cell) {
    // the first arg to this function is a string of all the cell's
    // innertext smashed together with no delimiters, so we need to find
    // the original cell and grab its first element to do the work
    var a = $(cell).find('li').first().text().split('.');
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
  if (!table.find("tbody tr:visible").length && typeof(template) !== "undefined") {
    colspan = table.find("th[colspan]").attr('colspan');
    params = {
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
      $table.find("thead th[class!='table_header']").each(function (i, val) {
        $th = $(this);
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
        } else if ($th.data('type') == 'naturalSort'){
          header_options[i] = {sorter: 'naturalSort'};
        }
      });
      $table.tablesorter({
        headers: header_options,
        widgets: ['zebra'],
        selectorHeaders: "thead th[class!='table_header']",
        cancelSelection: false
      });
    }
  });
};

horizon.datatables.add_table_checkboxes = function(parent) {
  $(parent).find('table thead .multi_select_column').each(function(index, thead) {
    if (!$(thead).find('.table-row-multi-select:checkbox').length &&
      $(thead).parents('table').find('tbody .table-row-multi-select:checkbox').length) {
      $(thead).append('<input type="checkbox" class="table-row-multi-select">');
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
      input.next('button.btn span.fa-search').on('click keypress', function (evt) {
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
          var template, table, colspan, params;
          table = $(table_selector);
          horizon.datatables.update_footer_count(table);
          horizon.datatables.add_no_results_row(table);
          horizon.datatables.fix_row_striping(table);
        },
        prepareQuery: function (val) {
          return new RegExp(val, "i");
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

horizon.addInitFunction(function() {
  horizon.datatables.validate_button();
  horizon.datatables.disable_buttons();
  $('table.datatable').each(function (idx, el) {
    horizon.datatables.update_footer_count($(el), 0);
  });
  horizon.datatables.initialize_checkboxes_behavior();

  // Trigger run-once setup scripts for tables.
  horizon.datatables.add_table_checkboxes($('body'));
  horizon.datatables.set_table_sorting($('body'));
  horizon.datatables.set_table_query_filter($('body'));
  horizon.datatables.set_table_fixed_filter($('body'));

  // Also apply on tables in modal views.
  horizon.modals.addModalInitFunction(horizon.datatables.add_table_checkboxes);
  horizon.modals.addModalInitFunction(horizon.datatables.set_table_sorting);
  horizon.modals.addModalInitFunction(horizon.datatables.set_table_query_filter);
  horizon.modals.addModalInitFunction(horizon.datatables.set_table_fixed_filter);

  // Also apply on tables in tabs views for lazy-loaded data.
  horizon.tabs.addTabLoadFunction(horizon.datatables.add_table_checkboxes);
  horizon.tabs.addTabLoadFunction(horizon.datatables.set_table_sorting);
  horizon.tabs.addTabLoadFunction(horizon.datatables.set_table_query_filter);
  horizon.tabs.addTabLoadFunction(horizon.datatables.set_table_fixed_filter);
  horizon.tabs.addTabLoadFunction(horizon.datatables.initialize_checkboxes_behavior);
  horizon.tabs.addTabLoadFunction(horizon.datatables.validate_button);

  horizon.datatables.update();
});
