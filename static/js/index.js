$(".tab").click(function () {
  var tabs = $(this).parent().parent().children();
  for (let i = 0; i < 3; i++) {
    tab = $(tabs[i]).children();
    if ($(tab).hasClass("active")){
      $(tab).removeClass("active");
    }
    if ($(tab).attr("aria-current") === "page"){
      $(tab).removeAttr("aria-current");
    }
  }
  $(this).addClass("active");
  $(this).attr("aria-current", "page")
})

var tabs = $('[data-tab-value]');
var tabInfos = $('[data-tab-info]');

for (let i = 0; i < 3; i++) {
    $(tabs[i]).click(function () {
        var target = $(tabs[i].dataset.tabValue);
        for (let i = 0; i < 3; i++) {
            $(tabInfos[i]).removeClass('active')
        }
        target.addClass('active');
        return false;
    })
}

setInterval(function(){
    var stat_height = $(".stat").outerHeight();
    $(".stats-card").innerHeight(stat_height * 5);
}, 1000);
