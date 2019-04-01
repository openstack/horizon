/**
 * Licensed under the Apache License, Version 2.0 (the "License"); you may
 * not use this file except in compliance with the License. You may obtain
 * a copy of the License at
 *
 *    http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
 * WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
 * License for the specific language governing permissions and limitations
 * under the License.
 */

/* Namespace for core functionality related to Forms. */
horizon.forms = {
  handle_snapshot_source: function() {
    $("div.table_wrapper, #modal_wrapper").on("change", "select#id_snapshot_source", function() {
      var $option = $(this).find("option:selected");
      var $form = $(this).closest('form');
      var $volName = $form.find('input#id_name');
      if ($volName.val() === "") {
        $volName.val($option.data("name"));
      }
      var $volSize = $form.find('input#id_size');
      var volSize = parseInt($volSize.val(), 10) || -1;
      var dataSize = parseInt($option.data("size"), 10) || -1;
      if (volSize < dataSize) {
        $volSize.val(dataSize);
      }
    });
  },

  handle_volume_source: function() {
    $("div.table_wrapper, #modal_wrapper").on("change", "select#id_volume_source", function() {
      var $option = $(this).find("option:selected");
      var $form = $(this).closest('form');
      var $volName = $form.find('input#id_name');
      if ($volName.val() === "") {
        $volName.val($option.data("name"));
      }
      var $volSize = $form.find('input#id_size');
      var volSize = parseInt($volSize.val(), 10) || -1;
      var dataSize = parseInt($option.data("size"), 10) || -1;
      if (volSize < dataSize) {
        $volSize.val(dataSize);
      }
    });
  },

  handle_image_source: function() {
    $("div.table_wrapper, #modal_wrapper").on("change", "select#id_image_source", function() {
      var $option = $(this).find("option:selected");
      var $form = $(this).closest('form');
      var $volName = $form.find('input#id_name');
      if ($volName.val() === "") {
        $volName.val($option.data("name"));
      }
      var $volSize = $form.find('input#id_size');
      var dataSize = parseInt($option.data("size"), 10) || -1;
      var minDiskSize = parseInt($option.data("min_disk"), 10) || 1;
      $volSize.val(Math.max(minDiskSize, dataSize));
    });
  },

  handle_subnet_address_source: function() {
    $("div.table_wrapper, #modal_wrapper").on("change", "select#id_address_source", function() {
      var $option = $(this).find("option:selected");
      var $form = $(this).closest("form");
      var $ipVersion = $form.find("select#id_ip_version");
      if ($option.val() == "subnetpool") {
        $ipVersion.attr("disabled", "disabled");
      } else {
        $ipVersion.removeAttr("disabled");
      }
    });
  },

  handle_subnet_subnetpool: function() {
    $("div.table_wrapper, #modal_wrapper").on("change", "select#id_subnetpool", function() {
      var $option = $(this).find("option:selected");
      var $form = $(this).closest("form");
      var $ipVersion = $form.find("select#id_ip_version");
      var $prefixLength = $form.find("select#id_prefixlen");
      var subnetpoolIpVersion = parseInt($option.data("ip_version"), 10) || 4;
      var minPrefixLen = parseInt($option.data("min_prefixlen"), 10) || 1;
      var maxPrefixLen = parseInt($option.data("max_prefixlen"), 10);
      var defaultPrefixLen = parseInt($option.data("default_prefixlen"), 10) ||
                             -1;
      var optionsAsString = "";

      $ipVersion.val(subnetpoolIpVersion);

      if (!maxPrefixLen) {
        if (subnetpoolIpVersion == 4) {
          maxPrefixLen = 32;
        } else {
          maxPrefixLen = 128;
        }
      }

      for (i = minPrefixLen; i <= maxPrefixLen; i++) {
        optionsAsString += "<option value='" + i + "'>" + i;
        if (i == defaultPrefixLen) {
          optionsAsString += " (" + gettext("pool default") + ")";
        }
        optionsAsString += "</option>";
      }
      $prefixLength.empty().append(optionsAsString);
      if (defaultPrefixLen >= 0) {
        $prefixLength.val(defaultPrefixLen);
      } else {
        $prefixLength.val("");
      }
    });
  },

  /**
   * In the container's upload object form, copy the selected file name in the
   * object name field if the field is empty. The filename string is stored in
   * the input as an attribute "filename". The value is used as comparison to
   * compare with the value of the new filename string.
   */
  handle_object_upload_source: function() {
    $("div.table_wrapper, #modal_wrapper").on("change", "input#id_object_file", function() {
      if (typeof($(this).attr("filename")) === 'undefined') {
        $(this).attr("filename", "");
      }
      var $form = $(this).closest("form");
      var $obj_name = $form.find("input#id_name");
      var $fullPath = $(this).val();
      var $startIndex = ($fullPath.indexOf('\\') >= 0 ? $fullPath.lastIndexOf('\\') : $fullPath.lastIndexOf('/'));
      var $filename = $fullPath.substring($startIndex);

      if ($filename.indexOf('\\') === 0 || $filename.indexOf('/') === 0) {
        $filename = $filename.substring(1);
      }

      if (typeof($obj_name.val()) === 'undefined' || $obj_name.val().length < 1 || $(this).attr("filename").localeCompare($obj_name.val()) === 0) {
        $obj_name.val($filename);
        $(this).attr("filename", $filename);
        $obj_name.trigger('input');
      }
    });
  },

  datepicker: function() {
    var startDate = $('#id_start').datepicker({ language: horizon.datepickerLocale })
      .on('changeDate', function(ev) {
        if (ev.dates[0].valueOf() > endDate.dates[0].valueOf()) {
          var newDate = new Date(ev.dates[0]);
          newDate.setDate(newDate.getDate() + 1);
          endDate.setDate(newDate);
          $('input#id_end')[0].focus();
        }
        startDate.hide();
        endDate.setStartDate(ev.dates[0]);
        endDate.update();
      }).data('datepicker');

    var endDate = $('#id_end').datepicker({
      language: horizon.datepickerLocale,
      startDate: startDate ? startDate.dates[0] : null
    }).on('changeDate', function() {
        endDate.hide();
      }).data('datepicker');

    $("#id_start").mousedown(function(){
      endDate.hide();
    });

    $("#id_end").mousedown(function(){
      startDate.hide();
    });

    $('.datepicker-addon').on('click', function() {
      $(this).siblings('input').trigger('focus');
    });
  }
};

horizon.forms.handle_submit = function (el) {
  var $form = $(el).find("form");
  $form.submit(function () {
    var $this = $(this);
    // Disable multiple submissions when launching a form.
    var button = $this.find('[type="submit"]');
    if (button.hasClass('btn-primary') && !button.hasClass('always-enabled')){
      $this.submit(function () {
        return false;
      });
      button.removeClass('primary').addClass('disabled');
      button.attr('disabled', 'disabled');
    }
    // Remove disabled attribute on select fields before submit to get value
    // included in POST request.
    $this.find('select[disabled="disabled"]').each(function (i, field) {
      $(field).removeAttr("disabled");
    });
    return true;
  });
};

horizon.forms.add_password_fields_reveal_buttons = function (el) {
  var _change_input_type = function ($input, type) {
    /*
     * In a perfect world, this function would just do:
     *
     *   $input.attr('type', type);
     *
     * however, Microsoft Internet Explorer exists and we have to support it.
     */

    var $new_input = $input.clone();

    $new_input.attr('type', type);
    $input.replaceWith($new_input);
    return $new_input;
  };


  $(el).find('input[type="password"]').each(function (i, input) {
    var $input = $(input);

    $input.closest('div').addClass("has-feedback");
    $('<span>').addClass(
      "form-control-feedback fa fa-eye password-icon"
    ).insertAfter($input).click(function () {
      var $icon = $(this);

      if ($input.attr('type') === 'password') {
        $icon.removeClass('fa-eye');
        $icon.addClass('fa-eye-slash');
        $input = _change_input_type($input, 'text');
      } else {
        $icon.removeClass('fa-eye-slash');
        $icon.addClass('fa-eye');
        $input = _change_input_type($input, 'password');
      }
    });
  });
};

horizon.forms.init_themable_select = function ($elem) {
  "use strict";

  // If not specified, find them all
  $elem = $elem || $('body');

  // If a jQuery object isn't passed in ... make it one
  $elem = $elem instanceof jQuery ? $elem : $($elem);

  // Pass in a container OR the themable select itself
  $elem = $elem.hasClass('themable-select') ? $elem : $elem.find('.themable-select');

  var initialized_class = 'select-initialized';

  if ($elem.hasClass(initialized_class)) {
    return;
  }

  $elem.addClass(initialized_class);

  // Update the select value if dropdown value changes
  $elem.on('click', 'li a', function () {
    var $this = $(this);
    var $container = $this.closest('.themable-select');
    var value = $this.data('selectValue');

    // Find select ... if we've searched for it before, then its cached on 'data-select'
    var $select = $container.data('mySelect');
    if (!$select) {
      $select = $container.find('select');
      $container.data('mySelect', $select);
    }

    // Set the select if necessary
    if($select.val() !== value) {
      $select.val(value).change();
    }
  });

  $elem.find('li a[title]').tooltip();

  // We need to rebuild the dropdown if the Select html ever
  // changes via javascript. Mutation Observers are DOM change
  // listeners. http://stackoverflow.com/a/11546242
  MutationObserver = window.MutationObserver || window.WebKitMutationObserver; // eslint-disable-line no-native-reassign

  var $targets = $elem.find('select');
  for (var ii = 0; ii < $targets.length; ii++) {
    var observer = new MutationObserver(function (mutations) { // eslint-disable-line no-loop-func

      // Will return many mutations for a select box changing,
      // we just need the target of one.
      var $select = $(mutations[0].target).closest('select');
      var $options = $select.find('option');
      var list = [];

      for (var jj = 0; jj < $options.length; jj++) {

        // Cache the jQuery Object
        var $thisOption = $($options[jj]);

        // Build new list item and anchor tag.
        var $list_item = $(document.createElement('li'))
            .attr('data-original-index', jj);

        var $anchor = $(document.createElement('a'))
          .attr('data-select-value', $thisOption.attr('value'));

        // Append option text to anchor, then to list item.
        $anchor.text($thisOption.text()).appendTo($list_item);
        list[jj] = $list_item;
      }

      // Add the new list to the dropdown.
      $select.siblings('.dropdown-menu').html(list).change();
      $select.trigger('change');
    });

    var config = {
      childList: true,
      subtree: true,
      attributes: false,
      characterData: true
    };

    observer.observe($targets[ii], config);
  }

  // Update the dropdown if select value changes
  $elem.children('select').on('change', function () {
    var $this = $(this);
    var thisVal = $this.val();
    var thisLabel = $this.find('option[value="' + thisVal + '"]').text();

    // Go find the title element
    var $title = $this.parents('.themable-select').find('.dropdown-title');

    // Set dropdown title to first option if the select menu is unset
    if (thisLabel === null || thisLabel.length === 0) {
      thisLabel = $this.find('option').first().text();
    }

    // Update the dropdown-title if necessary.
    if (thisLabel !== $title.text()) {
      $title.text(thisLabel);
    }
  });
};

horizon.forms.init_new_selects = function () {
  $(document).on('DOMNodeInserted', function(e) {
    var $target = $(e.target);
    var newInputs = $target.find('.themable-select').not('.select-initialized');
    for (var ii = 0; ii < newInputs.length; ii++) {
      horizon.forms.init_themable_select($(newInputs[ii]));
    }
  });
};

horizon.forms.getSpinnerValue = function(val, defaultVal) {
  val = parseInt(val, 10);
  return isNaN(val) ? defaultVal : val;
};

horizon.forms.checkSpinnerValue = function($inputs) {
  $inputs.each(function (index, input) {
    var $input = $(input);
    var val = $input.attr('value');
    var max = horizon.forms.getSpinnerValue($input.attr('max'), Number.MAX_SAFE_INTEGER);
    var min = horizon.forms.getSpinnerValue($input.attr('min'), 0);

    var $parent = $input.parents('.themable-spinner');
    var $up = $parent.find('.spinner-up');
    var $down = $parent.find('.spinner-down');

    $parent.find('.themable-spinner-btn').removeAttr('disabled');
    if (val <= min) {

      // Disable if we've hit the min
      $down.attr('disabled', true);
    } else if (val >= max) {

      // Disable if we've hit the max
      $up.attr('disabled', true);
    }
  });
};

horizon.forms.init_themable_spinner = function ($elem) {
  "use strict";

  // If not specified, find them all
  $elem = $elem || $('body');

  // If a jQuery object isn't passed in ... make it one
  $elem = $elem instanceof jQuery ? $elem : $($elem);

  // Pass in a container OR the themable spinner itself
  $elem = $elem.hasClass('themable-spinner') ? $elem : $elem.find('.themable-spinner');

  // Remove elements already initialized
  var initialized_class = 'spinner-initialized';
  $elem = $elem.not('.' + initialized_class);

  var $input = $elem.find('input[type="number"]');
  horizon.forms.checkSpinnerValue($input);

  $elem.addClass(initialized_class)
    .on('click', '.btn', function() {
      var $this = $(this);
      var $input = $this.parents('.themable-spinner').find('input');
      var max = horizon.forms.getSpinnerValue($input.attr('max'), Number.MAX_SAFE_INTEGER);
      var min = horizon.forms.getSpinnerValue($input.attr('min'), 0);
      var step = horizon.forms.getSpinnerValue($input.attr('step'), 1);
      var originalVal = $input.val();
      var val = parseInt(originalVal === '' ? min || 0 : $input.val(), 10);

      var new_val = val - step;
      if ($this.hasClass('spinner-up')) {
        new_val = originalVal ? val + step : min;

        // Increase the step if we can
        if (max == undefined || new_val <= max) {
          $input.val(new_val).trigger('input').trigger('change');
        }

      } else {
        new_val = originalVal ? val - step : min;

        // Decrease the step if we can
        if (min == undefined || new_val >= min) {
          $input.val(new_val).trigger('input').trigger('change');
        }
      }
    });

  $input.on('change', function(e) {
    horizon.forms.checkSpinnerValue($(e.delegateTarget));
  });
};

horizon.forms.init_new_spinners = function () {
  $(document).on('DOMNodeInserted', function(e) {
    var $target = $(e.target);
    var newInputs = $target.find('.themable-spinner').not('.spinner-initialized');
    for (var ii = 0; ii < newInputs.length; ii++) {
      horizon.forms.init_themable_spinner($(newInputs[ii]));
    }
  });
};

horizon.addInitFunction(horizon.forms.init = function () {
  var $body = $('body');
  horizon.forms.handle_submit($body);
  horizon.modals.addModalInitFunction(horizon.forms.handle_submit);

  horizon.forms.init_themable_select();
  horizon.forms.init_new_selects();
  horizon.modals.addModalInitFunction(horizon.forms.init_themable_select);

  horizon.forms.init_themable_spinner();
  horizon.forms.init_new_spinners();

  horizon.forms.handle_snapshot_source();
  horizon.forms.handle_volume_source();
  horizon.forms.handle_image_source();
  horizon.forms.handle_object_upload_source();
  horizon.forms.datepicker();
  horizon.forms.handle_subnet_address_source();
  horizon.forms.handle_subnet_subnetpool();

  if (!horizon.conf.disable_password_reveal) {
    horizon.forms.add_password_fields_reveal_buttons($body);
    horizon.modals.addModalInitFunction(
      horizon.forms.add_password_fields_reveal_buttons);
  }

  // Bind event handlers to confirm dangerous actions.
  // Stops angular form buttons from triggering this event
  $body.on("click", "form button:not([ng-click]).btn-danger", function (evt) {
    horizon.datatables.confirm(this);
    evt.preventDefault();
  });

  /* Switchable Fields (See Horizon's Forms docs for more information) */

  // Single reference
  var $document = $(document);

  // Bind handler for swapping labels on "switchable" select fields.
  $document.on("change", 'select.switchable', function (evt) {
    var $fieldset = $(evt.target).closest('fieldset'),
      $switchables = $fieldset.find('select.switchable');

    $switchables.each(function (index, switchable) {
      var $switchable = $(switchable);
      var slug = $switchable.data('slug');
      var isThemable = $switchable.parent('.themable-select').length > 0;
      var visible = isThemable
        ? $switchable.siblings('.dropdown-toggle').is(':visible')
        : $switchable.is(':visible');
      var val = $switchable.val();

      function handle_switched_field(index, input){
        var $input = $(input),
          data = $input.data(slug + "-" + val);

        if (typeof data === "undefined" || !visible) {
          $input.closest('.form-group').hide();
          //The required verification should be removed and recorded
          if ($input.attr('required') === 'required') {
            $input.data('savedRequired', 'required');
            $input.removeAttr('required');
          }
        } else {
          //If the input is a checkbox no need to replace html for label since it has another structure
          if($input.attr('type') !== "checkbox"){
            $('label[for=' + $input.attr('id') + ']').html(data);
          }
          $input.closest('.form-group').show();
          //Add the required verification if it is required
          if ($input.data('savedRequired') === 'required') {
            $input.attr("required", "required");
          }
        }
        if ($input.data("required-when-shown") === true &&
            $input.closest('.form-group').find('.hz-icon-required').length < 1) {
          var asterist_text = '<span class="hz-icon-required fa fa-asterisk"></span>';
          $input.closest('.form-group').children('.control-label').after(asterist_text);
        }
      }

      $fieldset.find('.switched[data-switch-on*="' + slug + '"]').each(handle_switched_field);
      $fieldset.siblings().find('.switched[data-switch-on*="' + slug + '"]').each(handle_switched_field);
    });
  });

  // Fire off the change event to trigger the proper initial values.
  $('select.switchable').trigger('change');
  // Queue up the for new modals, too.
  horizon.modals.addModalInitFunction(function (modal) {
    $(modal).find('select.switchable').trigger('change');
  });

  // Bind handler for swapping labels on "switchable" checkbox input fields.
  $document.on("change", 'input.switchable', function (evt) {
    var $fieldset = $(evt.target).closest('fieldset'),
      $switchables = $fieldset.find('input.switchable');

    $switchables.each(function (index, switchable) {
      var $switchable = $(switchable),
        visible = $switchable.parent().hasClass('themable-checkbox') ? $switchable.siblings('label').is(':visible') : $switchable.is(':visible'),
        slug = $switchable.data('slug'),
        checked = $switchable.prop('checked'),
        hide_on = $switchable.data('hideOnChecked');

      // If checkbox is hidden then do not apply any further logic
      if (!visible) return;

      // If the checkbox has hide-tab attribute then hide/show the tab
      if ($switchable.data('hide-tab')){
        var hide_tab = String($switchable.data('hide-tab')).split(',');
        for (var i = 0, len = hide_tab.length; i < len; i++) {
          var tab = $('*[data-target="#'+ hide_tab[i] +'"]').parent();
          if(checked == hide_on) {
            // If the checkbox is not checked then hide the tab
            tab.hide();
          } else if (!tab.is(':visible')) {
            // If the checkbox is checked and the tab is currently hidden then show the tab again
            tab.show();
          }
        }

        // hide/show button-next or button-final
        var $btnfinal = $('.button-final');
        if(checked == hide_on) {
          $('.button-next').hide();
          $btnfinal.show();
          $btnfinal.data('show-on-tab', $fieldset.prop('id'));
        } else{
          $btnfinal.hide();
          $('.button-next').show();
          $btnfinal.removeData('show-on-tab');
        }
      }

      function handle_switched_field(index, input){
        var $input = $(input);

        if (checked != hide_on) {
          $input.closest('.form-group').show();
          // Add the required class to form group to show a (*) next to label
          if ($input.data('is-required')) {
            $input.closest('.form-group').addClass("required");
          }
        } else {
          $input.closest('.form-group').hide();
          if ($input.data('is-required')) {
            $input.closest('.form-group').removeClass("required");
          }
        }
      }

      $fieldset.find('.switched[data-switch-on*="' + slug + '"]').each(handle_switched_field);
      $fieldset.siblings().find('.switched[data-switch-on*="' + slug + '"]').each(handle_switched_field);
    });
  });

  // Fire off the change event to trigger the proper initial values.
  $('input.switchable').trigger('change');
  // Queue up the for new modals, too.
  horizon.modals.addModalInitFunction(function (modal) {
    $(modal).find('input.switchable').trigger('change');
  });

  $document.on('shown.bs.tab', function() {
    var $fieldset = $('fieldset.active');
    var $btnfinal = $('.button-final');
    if ($btnfinal.data('show-on-tab')) {
      if ($fieldset.prop('id') == $btnfinal.data('show-on-tab')) {
        $('.button-next').hide();
        $btnfinal.show();
      } else {
        $btnfinal.hide();
        $('.button-next').show();
      }
    }
  });

  /* Help tooltips */

  // Apply standard handler for everything but checkboxes.
  $document.tooltip({
    selector: "div.form-group .help-icon",
    placement: function (tip, input) {
      // Position to the right unless this is a "split" for in which case put
      // the tooltip below so it doesn't block the next field.
      return $(input).closest("form[class*='split']").length ? "bottom" : 'right';
    },
    title: function () {
      return $(this).closest('div.form-group').children('.help-block').text();
    }
  });
  // Hide the tooltip upon interaction with the field for select boxes.
  // We use mousedown and keydown since those "open" the select dropdown.
  $document.on('mousedown keydown', '.form-group select', function () {
    $(this).tooltip('hide');
  });
  // Hide the tooltip after escape button pressed
  $document.on('keydown.esc_btn', function (evt) {
    if (evt.keyCode === 27) {
      $('.tooltip').hide();
    }
  });

  // Hide the help text for js-capable browsers
  $('p.help-block').hide();
});
