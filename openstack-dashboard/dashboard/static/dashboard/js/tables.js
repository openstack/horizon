horizon.addInitFunction(function() {
  $('td.actions ul').mouseleave(function(){
    $(this).parent().find('a.more-actions').removeClass('active')
    $(this).removeClass('active');
  });

  $('.table_search input').quicksearch('tr.odd, tr.even', {
    'delay': 300,
    'loader': 'span.loading',
    'bind': 'keyup click',
    'show': function () {
      this.style.color = '';
    },
    'hide': function () {
      this.style.display = 'none';
    },
    'prepareQuery': function (val) {
      return new RegExp(val, "i");
    },
    'testQuery': function (query, txt, _row) {
      return query.test($(_row).find('td:not(.hidden)').text());
    }
  });

  $('table.sortable').tablesorter();

  // Actions button dropdown behavior
  $('a.more-actions').mouseenter(function() {
    $(this).addClass('active')
    $('td.actions ul').each(function(){
      // If another dropdown is open, close it.
      if ($(this).hasClass('active')) {
        $(this).removeClass('active')
        $(this).parent().find('a.more-actions').removeClass('active')
      };
    });
    $(this).parent().find('ul').addClass('active');
  });
});
