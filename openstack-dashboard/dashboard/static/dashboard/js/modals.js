horizon.addInitFunction(function() {
  $(document).on('click', '.modal:not(.static_page) .cancel', function (evt) {
    $(this).closest('.modal').remove();
    return false;
  });

  $('.ajax-modal').click(function (evt) {
    var $this = $(this);
    $.ajax($this.attr('href'), {
      complete: function (jqXHR, status) {
        $('body').append(jqXHR.responseText);
        $('.modal span.help-block').hide();
        $('.modal:last').modal({'show':true, 'backdrop': true, 'keyboard': true});

        // TODO(tres): Find some better way to deal with grouped form fields.
        var volumeField = $("#id_volume");
        if(volumeField) {
          var disclosureElement = $("<div />").addClass("volume_boot_disclosure").text("Boot From Volume");
          var volumeContainer = volumeField.parent().parent();
          var deviceContainer = $("#id_device_name").parent().parent();
          var deleteOnTermContainer = $("#id_delete_on_terminate").parent().parent();

          volumeContainer.before(disclosureElement);

          disclosureElement.click(function() {
            if(volumeContainer.hasClass("hide")) {
              disclosureElement.addClass("on");
              volumeContainer.removeClass("hide");
              deviceContainer.removeClass("hide");
              deleteOnTermContainer.removeClass("hide");
            } else {
              disclosureElement.removeClass("on");
              volumeContainer.addClass("hide");
              deviceContainer.addClass("hide");
              deleteOnTermContainer.addClass("hide");
            }
          });

          volumeContainer.addClass("hide");
          deviceContainer.addClass("hide");
          deleteOnTermContainer.addClass("hide");
        }
      }
    });
    return false;
  });
});
