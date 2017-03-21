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

/*
  Used for animating and displaying quota information on forms using
  D3js progress bars. Also used for displaying flavor details on modal-
  dialogs.

  Usage:
    In order to have progress bars that work with this, you need to have a
    DOM structure like this in your Django template:

    <div id="your_progress_bar_id" class="quota_bar">
    </div>

    With this progress bar, you then need to add some data- HTML attributes
    to the div #your_progress_bar_id. The available data- attributes are:

      data-quota-used="integer" REQUIRED
        Integer representing the total number used by the user.

      data-quota-limit="integer" REQUIRED
        Integer representing the total quota limit the user has. Note this IS
        NOT the amount remaining they can use, but the total original quota.

      ONE OF THE THREE ATTRIBUTES BELOW IS REQUIRED:

      data-progress-indicator-step-by="integer" OPTIONAL
        Indicates the numeric unit the quota JavaScript should automatically
        animate this progress bar by on load. Can be used with the other
        data- attributes.

        A good use-case here is when you have a modal dialog to create ONE
        volume, and you have a progress bar for volumes, but there are no
        form elements that represent that number (as it is not settable by
        the user.)

      data-progress-indicator-for="html_id_of_form_input"
        Tells the quota JavaScript which form element on this page is tied to
        this progress indicator. If this form element is an input, it will
        automatically fire on "keyup" in that form field, and change this
        progress bar to denote the numeric change.

      data-progress-indicator-flavor
        This attribute is used to tell this quota JavaScript that this
        progress bar is controller by an instance flavor select form element.
        This attribute takes no value, but is used and configured
        automatically by this script to update when a new flavor is chosen
        by the end-user.
 */
horizon.Quota = {
  is_flavor_quota: false, // Is this a flavor-based quota display?
  user_value_progress_bars: [], // Progress bars triggered by user-changeable form elements.
  auto_value_progress_bars: [], // Progress bars that should be automatically changed.
  flavor_progress_bars: [], // Progress bars that relate to flavor details.
  user_value_form_inputs: [], // The actual form inputs that trigger progress changes.
  selected_flavor: null, // The flavor object of the current selected flavor on the form.
  flavors: [], // The flavor objects the form represents, passed to us in initWithFlavors.

  /*
   Determines the progress bars and form elements to be used for quota
   display. Also attaches handlers to the form elements as well as performing
   the animations when the progress bars first load.
   */
  init: function() {
    this.user_value_progress_bars = $('div[data-progress-indicator-for]');
    this.auto_value_progress_bars = $('div[data-progress-indicator-step-by]');
    this.user_value_form_inputs = $($.map(this.user_value_progress_bars, function(elm) {
      return ('#' + $(elm).attr('data-progress-indicator-for'));
    }));

    this._attachInputHandlers();
  },

  /*
   Confirm that the specified attribute 'actual' meets
   or exceeds the specified value 'minimum'.
   */
  belowMinimum: function(minimum, actual) {
    return parseInt(minimum, 10) > parseInt(actual, 10);
  },

  /*
   Determines if the selected image meets the requirements of
   the selected flavor.
   */
  imageFitsFlavor: function(image, flavor) {
    if (image === undefined) {
      /*
       If we don't actually have an image, we don't need to
       limit our flavors, so we return true in this case.
       */
      return true;
    } else {
      var overDisk = horizon.Quota.belowMinimum(image.min_disk, flavor.disk);
      var overRAM = horizon.Quota.belowMinimum(image.min_ram, flavor.ram);
      return !(overDisk || overRAM);
    }
  },

  /*
   Note to the user that some flavors have been disabled.
   */
  noteDisabledFlavors: function(allDisabled) {
    if ($('#some_flavors_disabled').length === 0) {
      var message = allDisabled ? horizon.Quota.allFlavorsDisabledMessage
        : horizon.Quota.disabledFlavorMessage;
      $('#id_flavor').parent().append("<span id='some_flavors_disabled'>" +
        message + '</span>');
    }
  },

  /*
   Re-enables all flavors that may have been disabled, and
   clear the message displayed about them being disabled.
   */
  resetFlavors: function() {
    if ($('#some_flavors_disabled')) {
      $('#some_flavors_disabled').remove();
      $('#id_flavor option').each(function() {
        $(this).attr('disabled', false);
      });
    }
  },

  /*
   A convenience method to find an image object by its id.
   */
  findImageById: function(id) {
    var _image;
    $.each(horizon.Quota.images, function(i, image){
      if(image.id === id) {
        _image = image;
      }
    });
    return _image;
  },

  /*
   Return an image/snapshot Object based on which image/snapshot ID is selected
   */
  getSelectedImageOrSnapshot: function(source_type) {
    var selected = $('#id_' + source_type + '_id option:selected').val();
    return horizon.Quota.findImageById(selected);
  },

  /*
   Disable any flavors for a given image/snapshot that do not meet
   its minimum RAM or disk requirements.
   */
  disableFlavorsForImage: function(source_type) {
    var source = horizon.Quota.getSelectedImageOrSnapshot(source_type);
    var to_disable = []; // an array of flavor names to disable

    horizon.Quota.resetFlavors(); // clear any previous messages

    $.each(horizon.Quota.flavors, function(i, flavor) {
      if (!horizon.Quota.imageFitsFlavor(source, flavor)) {
        to_disable.push(flavor.name);
      }
    });

    var flavors = $('#id_flavor option');
    // Now, disable anything from above:
    $.each(to_disable, function(i, flavor_name) {
      flavors.each(function(){
        if ($(this).text() === flavor_name) {
          $(this).attr('disabled', 'disabled');
        }
      });
    });

    // And then, finally, clean up:
    if (to_disable.length > 0) {
      var selected = ($('#id_flavor option').filter(':selected'))[0];
      if (to_disable.length < flavors.length && selected.disabled) {
        // we need to find a new flavor to select
        flavors.each(function(index, element) {
          if (!element.disabled) {
            $('#id_flavor').val(element.value);
            $('#id_flavor').change(); // force elements to update
            return false; // break
          }
        });
      }
      horizon.Quota.noteDisabledFlavors(to_disable.length === flavors.length);
    }
  },

  /*
   Store an array of image objects
   */
  initWithImages: function(images, disabledMessage, allDisabledMessage) {
    this.images = images;
    this.disabledFlavorMessage = disabledMessage;
    this.allFlavorsDisabledMessage = allDisabledMessage;
    // Check if the image is pre-selected
    horizon.Quota.disableFlavorsForImage('image');
  },

  /*
   Sets up the quota to be used with flavor form selectors, which requires
   some different handling of the forms. Also calls init() so that all of the
   other animations and handlers are taken care of as well when initializing
   with this method.
   */
  initWithFlavors: function(flavors) {
    this.is_flavor_quota = true;
    this.flavor_progress_bars = $('div[data-progress-indicator-flavor]');
    this.flavors = flavors;

    this.init();

    this.showFlavorDetails();
    this.updateFlavorUsage();
  },

  // Returns the flavor object for the selected flavor in the form.
  // also find out if there is old_flavor
  getSelectedFlavor: function() {
    if(this.is_flavor_quota) {
      this.selected_flavor = $.grep(this.flavors, function(flavor) {
        return flavor.id === $("#id_flavor").children(":selected").val();
      })[0];

      this.old_flavor = $.grep(this.flavors, function(flavor) {
        return flavor.name === $('#id_old_flavor_name').val();
      })[0];
    } else {
      this.old_flavor = null;
      this.selected_flavor = null;
    }

    return this.selected_flavor;
  },

  /*
   Populates the flavor details table with the flavor attributes of the
   selected flavor on the form select element.
   */
  showFlavorDetails: function() {
    this.getSelectedFlavor();

    if (this.selected_flavor) {
      var vcpus = horizon.Quota.humanizeNumbers(this.selected_flavor.vcpus);
      var disk = horizon.Quota.humanizeNumbers(this.selected_flavor.disk);
      var ephemeral = horizon.Quota.humanizeNumbers(this.selected_flavor["OS-FLV-EXT-DATA:ephemeral"]);
      var disk_total = this.selected_flavor.disk + this.selected_flavor["OS-FLV-EXT-DATA:ephemeral"];
      var disk_total_display = horizon.Quota.humanizeNumbers(disk_total);
      var ram = horizon.Quota.humanizeNumbers(this.selected_flavor.ram);

      $("#flavor_name").text(this.selected_flavor.name);
      $("#flavor_vcpus").text(vcpus);
      $("#flavor_disk").text(disk);
      $("#flavor_ephemeral").text(ephemeral);
      $("#flavor_disk_total").text(disk_total_display);
      $("#flavor_ram").text(ram);
    }
    else {//if change to nothing selected
      $("#flavor_name").html('');
      $("#flavor_vcpus").text('');
      $("#flavor_disk").text('');
      $("#flavor_ephemeral").text('');
      $("#flavor_disk_total").text('');
      $("#flavor_ram").text('');
    }
  },

  /*
   * Adds commas to any integer or numbers within a string for human display.
   * The number formatting depends on what language the user choose in Horizon
   * settings.
   *
   * Example:
   *   Default:
   *     horizon.Quota.humanizeNumbers(1234); -> "1,234"
   *     horizon.Quota.humanizeNumbers("My Total: 1234"); -> "My Total: 1,234"
   *
   *   If the user change the language to "Deutsch (de)":
   *     horizon.Quota.humanizeNumbers(1234); -> "1.234"
   *     horizon.Quota.humanizeNumbers("My Total: 1234"); -> "My Total: 1.234"
   *
   *   If the user change the language to "Français (fr)":
   *     horizon.Quota.humanizeNumbers(1234); -> "1 234"
   *     horizon.Quota.humanizeNumbers("My Total: 1234"); -> "My Total: 1 234"
   *
   */
  humanizeNumbers: function (number) {
    return number.toString().replace(/\d+(?:\.\d+)?/g, function(match) {
      var lang = horizon.cookies.get('horizon_language');
      try {
        return new Intl.NumberFormat(lang).format(match);
      } catch(e) {
        return match;
      }
    });
  },

  /*
   When a new flavor is selected, this takes care of updating the relevant
   progress bars associated with the flavor quota usage.
   */
  updateFlavorUsage: function() {
    if (!this.is_flavor_quota) { return; }

    var scope = this;
    var instance_count = (parseInt($("#id_count").val(), 10) || 1);
    var update_amount = 0;

    this.getSelectedFlavor();

    $(this.flavor_progress_bars).each(function(index, element) {
      var element_id = $(element).attr('id');
      var progress_stat = element_id.match(/^quota_(.+)/)[1];
      var sourceType = $("#id_source_type").val();
      var createVolume = (sourceType === "volume_snapshot_id" || sourceType === "volume_image_id");

      if (!progress_stat) {
        return;
      } else if (progress_stat === 'resize_instance') {
        // There is no instance added for resize.
        update_amount = 0;
      } else if (progress_stat === 'instances') {
          update_amount = instance_count;
      } else if (progress_stat === 'vcpus' &&
                 scope.old_flavor &&
                 scope.selected_flavor) {
        // Dealing with resizing instance where update_amount should be the
        // difference of old and new vcpus.
        var old_vcpus = scope.old_flavor.vcpus;
        var new_vcpus = scope.selected_flavor.vcpus;
        // If the user changes to a smaller flavor, it will not make any change
        // in the progress bar.
        // The default kvm doesn't seem to support downgrading to a smaller
        // flavor. Same comments apply to changing ram.
        update_amount =
              (new_vcpus - old_vcpus < 0) ? 0 : (new_vcpus - old_vcpus);
      } else if (progress_stat === 'ram' &&
                 scope.old_flavor &&
                 scope.selected_flavor) {
        // Dealing with resizing instance where update_amount should be the
        // difference of old and new ram.
        var old_ram = scope.old_flavor.ram;
        var new_ram = scope.selected_flavor.ram;
        update_amount = (new_ram - old_ram < 0) ? 0 : (new_ram - old_ram);
      } else if (progress_stat === "volume") {
        update_amount = createVolume ? instance_count : 0;
      } else if (progress_stat === "volume_storage") {
        var volumeSize = 0;

        if (sourceType === "volume_snapshot_id") {
          // get volume size from the selected snapshot
          var volumeSizeMatches = $("#id_volume_snapshot_id").children(":selected").html().match(/\s(\d+)\s/g);
          volumeSize = horizon.Quota.getSelectedFlavor().disk; // set volume size as the minimum flavor size
          if(volumeSizeMatches) {
            volumeSize = Math.max(volumeSize, volumeSizeMatches[volumeSizeMatches.length - 1]);
          }
        } else if (sourceType === "volume_image_id") {
          volumeSize = $("#id_volume_size").val();
        }

        update_amount = volumeSize * instance_count;
      } else if (scope.selected_flavor) {
        update_amount = (scope.selected_flavor[progress_stat] * instance_count);
      }

      scope.updateUsageFor(element, update_amount);
    });
  },

  // Does the math to calculate what percentage to update a progress bar by.
  updateUsageFor: function(progress_element, increment_by) {
    var $progress_element = $(progress_element);

    //var update_indicator = progress_element.find('.progress_bar_selected');
    var quota_limit = parseInt($progress_element.attr('data-quota-limit'), 10);
    var percentage_to_update = ((increment_by / quota_limit) * 100);

    this.update($progress_element.attr('id'), percentage_to_update);
  },

  // Update the progress Bar
  update: function(element, value) {

    // Find Progress Bars, we'll need both of them
    var bars = $('#' + element).find('.progress-bar');

    // Determine how much is already used -> this is the first bar
    // Also, convert it to an int ;)
    var used_val = +$(bars[0]).attr('aria-valuenow');

    // Calculate new total
    var total = used_val + value;

    // Make sure to normalize the value to 100 or less
    if (total > 100) {
      value = 100 - used_val;
    }

    // Turn percentage into a proper percentage string for style
    var percent_str = value + '%';

    // jQuery construct it and then cache it, we need it more than once
    var $bar = $(bars[1]);

    // Update the second progress bar
    $bar.css('width', percent_str)
      .attr('aria-valuenow', value)
      .find('.sr-only')
      .html(percent_str);

    // If the value is going to set total to 100+, set danger class
    if (total > 99) {
      $bar.removeClass('progress-bar-warning').addClass('progress-bar-danger');
    } else {
      $bar.removeClass('progress-bar-danger');

      /*eslint-disable */
      total > 89 ?
        $bar.addClass('progress-bar-warning') :
        $bar.removeClass('progress-bar-warning');
      /*eslint-enable */
    }
  },

  /*
   Attaches event handlers for the form elements associated with the
   progress bars.
   */
  _attachInputHandlers: function() {
    var scope = this;

    if(this.is_flavor_quota) {
      var eventCallback = function() {
        scope.showFlavorDetails();
        scope.updateFlavorUsage();
      };

      var imageChangeCallback = function() {
        scope.disableFlavorsForImage('image');
      };

      var snapshotChangeCallback = function() {
        scope.disableFlavorsForImage('instance_snapshot');
      };

      var volumeChangeCallback = function() {
        scope.updateFlavorUsage();
      };

      $('#id_flavor').on('keyup change', eventCallback);
      $('#id_count').on('input', eventCallback);
      $('#id_image_id').on('change', imageChangeCallback);
      $('#id_instance_snapshot_id').on('change', snapshotChangeCallback);
      $('#id_source_type').on('change', volumeChangeCallback);
      $('#id_volume_snapshot_id').on('change', volumeChangeCallback);
      $('#id_image_id').on('change', volumeChangeCallback);
      $('#id_volume_size').on('keyup change', volumeChangeCallback);
    }

    $(this.user_value_form_inputs).each(function(index, element) {
      $(element).on('input', function() {
        var $this = $(this);
        var $progress_element = $('div[data-progress-indicator-for=' + $this.attr('id') + ']');
        var integers_in_input = $this.val().match(/\d+/g);
        var user_integer;

        if(integers_in_input === null) {
          user_integer = 0;
        } else if(integers_in_input.length > 1) {
          /*
           Join all the numbers together that have been typed in. This takes
           care of junk input like "dd8d72n3k" and uses just the digits in
           that input, resulting in "8723".
           */
          user_integer = integers_in_input.join('');
        } else if(integers_in_input.length === 1) {
          user_integer = integers_in_input[0];
        }

        var progress_amount = parseInt(user_integer, 10);

        scope.updateUsageFor($progress_element, progress_amount);
      });
    });
  }
};
