$(function(){
  $('input#table_search').quicksearch('table tbody.main tr');
  
  $("#more").hide()  
  $("#page_header a.more_link").click(function(e){  
    $("#more").fadeToggle("slow")
    e.preventDefault();
  })
  
  $("#health_table tr").hide()
  $("#health_table tr:first").show()
  $("#health_table tr.odd, #health_table tr.even").show()
  
  $("#health_table .more_link").click(function(e){
    $(this).parent().parent().nextUntil(".even, .odd").fadeToggle("slow")
    e.preventDefault();
  })
  
  // $(".modal_window").hide()
  
  $("#weight_slider").slider()
  
  $('a.fancy_btn').click(function(e) {
		e.preventDefault();
	
		var maskHeight = $(document).height();
		var maskWidth = $(window).width();
	
		$('#mask').css({'width':maskWidth,'height':maskHeight});
		$('#mask').fadeTo(500, 0.7);	
	
		var winH = $(window).height();
		var winW = $(window).width();
              
		$(".modal_window").css('top',  winH/2-$(".modal_window").height()/2);
		$(".modal_window").css('left', winW/2-$(".modal_window").width()/2);
	
		$(".modal_window").fadeIn(1000); 
	
	});
	
  
})
