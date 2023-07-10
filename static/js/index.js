$(".tab").click(function () {
  var tabs = $(this).parent().parent().children();
  for (let i = 0; i < 4; i++) {
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

for (let i = 0; i < 4; i++) {
    $(tabs[i]).click(function () {
        var target = $(tabs[i].dataset.tabValue);
        for (let i = 0; i < 4; i++) {
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

handleScroll = (e) => {
    if (e.target.classList.contains("on-scrollbar") === false) {
        e.target.classList.add("on-scrollbar");
        setInterval(function(){
            e.target.classList.remove("on-scrollbar");
        }, 4000);
    }
    if ($(e.target).scrollTop() != 0){
        e.target.classList.add("not-top");
    } else if (e.target.classList.contains("not-top") === true) {
        e.target.classList.remove("not-top");
    }
}
window.addEventListener('scroll', this.handleScroll, true);

//Head to head
$('.stat-toggle').click(function(){
    var inputValue = $(this).attr("id");
    var targetBox = $("." + inputValue);
    $(".h2h-div").not(targetBox).addClass("hide");
    $(targetBox).removeClass("hide");
});
