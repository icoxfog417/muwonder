var _vm = null;

$(function(){
    //create widget
    var iframe   = document.querySelector('#soundcloudwdg');
    var url = $("#tracks-pager").find("a").first().data("resource-url");

    iframe.src = location.protocol + "//w.soundcloud.com/player/?url=" + url;
    widget = SC.Widget(iframe);
    widget.bind(SC.Widget.Events["PLAY"],function(){
        _vm.isPlaying(true);
    })
    widget.bind(SC.Widget.Events["PAUSE"],function(){
        _vm.isPlaying(false);
    })

    //make slides
    slider = $("#tracks").bxSlider({
        prevSelector: "#btnPrev",
        nextSelector: "#btnNext",
        prevText: "<i class='fa fa-fast-backward'></i>",
        nextText: "<i class='fa fa-fast-forward'></i>",
        minSlides: 1,
        maxSlides: 1,
        moveSlides: 1,
        pagerCustom: "#tracks-pager",
        onSlideBefore:function($slideElement, oldIndex, newIndex){
            _vm.widgetLoadByIndex(newIndex);
        }
    });

    //get criticizm
    var criticize = ["faster tempo", "more calm", "more recent"]
    function mwViewModel(widget, slider) {
        var self = this;
        self._widget = widget;
        self._slider = slider;

        self.isPlaying = ko.observable(false);
        self.criticize = ko.observableArray([
            "faster tempo", "more calm", "more recent"
        ]);

        self.widgetPlay = function(){
            if(self.isPlaying()){
                self._widget.pause();
            }else{
                self._widget.play();
            }
            self.isPlaying(!self.isPlaying());
        }

        self.widgetLoadByIndex = function(index){
            var element = $("#tracks-pager").find("a[data-slide-index='" + index + "']");
            var url = $(element).data("resource-url");
            self.widgetLoad(url, self.isPlaying());
        }

        self.widgetLoad = function(url, isAutoLoad){
            if(isAutoLoad){
                self._widget.load(url, {auto_play:true});
            }else{
                self._widget.load(url);
            }
        }

    }
    _vm = new mwViewModel(widget, slider);
    ko.applyBindings(_vm);

    /*
    $("#criticize").text(criticize[0]);
    var circleWidth = 200;

    $("#tempo").knob({
        min : 0,
        max : criticize.length,
        width: circleWidth,
        cursor: circleWidth * Math.PI / (2 * criticize.length),
        change : function (value) {
            if(value < criticize.length){
                $("#criticize").text(criticize[value]);
            }else{
                $("#criticize").text(criticize[0]);
            }
        }
    });
    */

})