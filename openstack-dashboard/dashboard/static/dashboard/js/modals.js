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
        $('body .modal:last').modal({'show':true, 'backdrop': true, 'keyboard': true});
      }
    });
    return false;
  });
});
