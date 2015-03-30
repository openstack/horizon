horizon.datepickers = {
  add: function(selector) {
    $(selector).each(function () {
      var el = $(this);
      el.datepicker({
        format: 'yyyy-mm-dd',
        setDate: new Date(),
        showButtonPanel: true,
        language: horizon.datepickerLocale
      });
    });
  }
};
