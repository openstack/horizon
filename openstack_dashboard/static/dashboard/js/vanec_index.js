 var showLogin = false;

 function init() {
     $('#mainbackground').height($(window).height());
     $('#mainbackground').width($(window).width());
     a = ($(window).width() - 324) / 2;
     b = ($(window).width() - 300) / 2;
     c = ($(window).width() - 250) / 2;
     if (!showLogin) {
         $('.logo').css("margin-left", a + "px");
     }
     // $('.login').fadeIn(1000);
 }

 $('.clickToLogin').click(function() {
     showLogin = true;
     $('.bottomItem').fadeOut("slow");
     $('.login').fadeIn(3000);
     $('.footer').fadeIn("slow");
     $('.logo').addClass("logoAnim");
     $('.logo').addClass("logoMove");
     $('.logo').css("margin-left", "20px");
     $('.logoCenter').addClass("logoCenterMove");
 });

 window.onload = init();
 $(window).on('resize', function() {
     init();
 });
