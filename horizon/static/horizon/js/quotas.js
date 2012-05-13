/* Update quota usage infographics when a flavor is selected to show the usage
 * that will be consumed by the selected flavor. */
horizon.updateQuotaUsages = function(flavors, usages) {
  var selectedFlavor = _.find(flavors, function(flavor) {
    return flavor.id == $("#id_flavor").children(":selected").val();
  });

  var selectedCount = parseInt($("#id_count").val(), 10);
  if(isNaN(selectedCount)) {
    selectedCount = 1;
  }

  // Map usage data fields to their corresponding html elements
  var flavorUsageMapping = [
    {'usage': 'instances', 'element': 'quota_instances'},
    {'usage': 'cores', 'element': 'quota_cores'},
    {'usage': 'gigabytes', 'element': 'quota_disk'},
    {'usage': 'ram', 'element': 'quota_ram'}
  ];

  var el, used, usage, width;
  _.each(flavorUsageMapping, function(mapping) {
    el = $('#' + mapping.element + " .progress_bar_selected");
    used = 0;
    usage = usages[mapping.usage];

    if(mapping.usage == "instances") {
      used = selectedCount;
    } else {
      _.each(usage.flavor_fields, function(flavorField) {
        used += (selectedFlavor[flavorField] * selectedCount);
      });
    }

    available = 100 - $('#' + mapping.element + " .progress_bar_fill").attr("data-width");
    if(used + usage.used <= usage.quota) {
      width = Math.round((used / usage.quota) * 100);
      el.removeClass('progress_bar_over');
    } else {
      width = available;
      if(!el.hasClass('progress_bar_over')) {
        el.addClass('progress_bar_over');
      }
    }

    el.animate({width: width + "%"}, 300);
  });

  // Also update flavor details
  $("#flavor_name").html(horizon.utils.truncate(selectedFlavor.name, 14, true));
  $("#flavor_vcpus").text(selectedFlavor.vcpus);
  $("#flavor_disk").text(selectedFlavor.disk);
  $("#flavor_ephemeral").text(selectedFlavor["OS-FLV-EXT-DATA:ephemeral"]);
  $("#flavor_disk_total").text(selectedFlavor.disk + selectedFlavor["OS-FLV-EXT-DATA:ephemeral"]);
  $("#flavor_ram").text(selectedFlavor.ram);
};

horizon.addInitFunction(function () {
  var quota_containers = $(".quota-dynamic");
  if (quota_containers.length) {
    horizon.updateQuotaUsages(horizon_flavors, horizon_usages);
  }
  $(document).on("change", "#id_flavor", function() {
    horizon.updateQuotaUsages(horizon_flavors, horizon_usages);
  });
  $(document).on("keyup", "#id_count", function() {
    horizon.updateQuotaUsages(horizon_flavors, horizon_usages);
  });
});
