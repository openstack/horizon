horizon.addInitFunction(function() {
  $(document).on('click', '.modal:not(.static_page) .cancel', function (evt) {
    $(this).closest('.modal').modal('hide');
    return false;
  });

  $('.ajax-modal').click(function (evt) {
    var $this = $(this);
    $.ajax($this.attr('href'), {
      complete: function (jqXHR, status) {
        $('body').append(jqXHR.responseText);
        $('.modal span.help-block').hide();
        $('.modal:last').modal();
        $('.modal:last').on('hidden', function () {
          $(this).remove();
        });

        // TODO(tres): Find some better way to deal with grouped form fields.
        var volumeField = $("#id_volume");
        if(volumeField) {
          var volumeContainer = volumeField.parent().parent();
          var deviceContainer = $("#id_device_name").parent().parent();
          var deleteOnTermContainer = $("#id_delete_on_terminate").parent().parent();

          function toggle_fields(show) {
            if(show) {
              volumeContainer.removeClass("hide");
              deviceContainer.removeClass("hide");
              deleteOnTermContainer.removeClass("hide");
            } else {
              volumeContainer.addClass("hide");
              deviceContainer.addClass("hide");
              deleteOnTermContainer.addClass("hide");
            }
          }

          if(volumeField.find("option").length == 1) {
            toggle_fields(false);
          } else {
            var disclosureElement = $("<div />").addClass("volume_boot_disclosure").text("Boot From Volume");

            volumeContainer.before(disclosureElement);

            disclosureElement.click(function() {
              if(volumeContainer.hasClass("hide")) {
                disclosureElement.addClass("on");
                toggle_fields(true);
              } else {
                disclosureElement.removeClass("on");
                toggle_fields(false);
              }
            });

            toggle_fields(false);
          }
        }
      }
    });

    return false;
  });
});
