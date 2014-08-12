var _vm = null;

$(function(){
    //create widget
    function initWidget(url){
        var iframe   = document.querySelector('#soundcloudwdg');
        iframe.src = location.protocol + "//w.soundcloud.com/player/?url=" + url;
        widget = SC.Widget(iframe);
        return widget;
    }

    //adjst size
    $(window).resize(function(){
        resizeContent()
    })

    function resizeContent(){
        var height = $(window).height();
        var minHeight = 100;
        var headerAndFooterHeight = 230 + 70 + 10;
        var mainHeight =  (height - headerAndFooterHeight > minHeight) ? height - headerAndFooterHeight : minHeight;
        $(".main").height(mainHeight);
    }
    resizeContent();

    //view model
    function mwViewModel() {
        var self = this;
        self._widget = null;
        self.API_TARGET = "/soundcloudapi/recommends/";

        self.isPlaying = ko.observable(false);
        self.trackIndex = ko.observable(0);
        self.criticizeIndex = ko.observable(0);
        self.tracks = ko.observableArray([]);
        self.criticize = ko.observableArray([]);

        self.session = ko.observableArray([]);
        self.guide = new MuGuide("muguide");
        self.guideMode = 0;
        self.isRetry = ko.observable(false);
        self.errorStatus = "";

        self.session_template = {
            track : "track-template",
            message : "message-template",
            taste : "taste-template",
            criticize : "criticize-template",
            sense : "sense-template",
            error : "error-template"
        }
        self.criticize_type = {
            proposed : 0,
            input : 1,
            taste : 2
        }
        self.guide_mode = {
            track : 0,
            taste : 1,
            proposed : 2
        }

        /*
         * show conversation
         */
        self.addSession = function(template, data){
            var s = {template:template, data:data};
            self.session.push(s);
        }
        self.setSession = function(template, data){
            self.session.removeAll();
            self.addSession(template, data);
        }

        /*
         * initialization
         */
        self.init = function(){
            self.guide.init();
            self.setSession(self.session_template.message,
                {message: "Let me introduce you the various genre tracks!\nPlease listen these."});

            //for Django csrf
            $.ajaxSetup({
                beforeSend: function(xhr, settings) {
                    if (!(/^(GET|HEAD|OPTIONS|TRACE)$/.test(settings.type)) && !this.crossDomain) {
                        var csrftoken = $.cookie('csrftoken');
                        xhr.setRequestHeader("X-CSRFToken", csrftoken);
                    }
                }
            });

            self.load("GET", {}, function(error){
                if(!error){
                    self.widgetLoadByIndex(0);
                }else{
                    self.isRetry(true);
                    self.guide.confuse();
                    self.setSession(self.session_template.message,
                        {message: "Oops, server cause error.\nPlease try again."});
                }
            });
        }

        /*
         * for track display
        */
        self.load = function(method, data, callback){
            self.isRetry(false);
            $.ajax({
                type: method,
                data: data,
                url: self.API_TARGET,
                dataType: "json"
            })
            .done(function(data) {
                var playing = null;
                if(self.isPlaying()){
                    playing = self.tracks(self.trackIndex());
                }

                if(data){
                    self.trackIndex(0);
                    self.criticizeIndex(0);
                    if(data.tracks.length > 0){
                        self.tracks.removeAll();
                        if(playing != null){
                            self.tracks.push(playing);
                        }
                        data.tracks.forEach(function(item){
                            self.tracks.push(item);
                        })
                    }

                    if(data.criticize.length > 0){
                        self.criticize.removeAll();
                        data.criticize.forEach(function(item){
                            self.criticize.push(item);
                        })
                    }
                }

                if(self._widget != null && self.tracks().length > 0 && !self.isPlaying()){
                    self.widgetLoadByIndex(0);
                }

                if(callback !== undefined){
                    callback();
                }
            })
            .fail(function(error) {
                console.log(error);
                if(callback !== undefined){
                    callback(error);
                }
            })
        }
        self.trackStyle = function(index){
            var css = "track";
            if(index == self.trackIndex()){
                css += " active";
            }
            return css;
        }

        /*
         * error handler
         */
        self.retry = function(){
            var errorOccured = self.errorStatus;
            self.errorStatus = "";
            self.init();
        }

        /*
         * for criticize
         */
        self.ask = function(){
            self.guideMode += 1;
            self.guideMode = self.guideMode % 3;
            self.showGuide(self.guideMode);
        }

        self.showGuide = function(mode){
            self.guideMode = mode;
            if(mode == self.guide_mode.track){
                self.setSession(self.session_template.track, self.tracks()[self.trackIndex()]);
            }else if(mode == self.guide_mode.taste){
                self.setSession(self.session_template.criticize, {text: "Do you like this Track?"});
            }else if(mode == self.guide_mode.proposed){
                self.setSession(self.session_template.criticize, self.criticize()[self.criticizeIndex()]);
            }else{
                self.setSession(self.session_template.track, self.tracks()[self.trackIndex()]);
            }
        }

        self.answer = function(answer){
            if(answer){
                var data = {
                    track_id: self.tracks()[self.trackIndex()].id
                };

                if(self.guideMode == self.guide_mode.taste){
                    data.criticize_type = self.criticize_type.taste;
                }else if(self.guideMode == self.guide_mode.proposed){
                    data.criticize_type = self.criticize_type.proposed;
                    data.value = self.criticize()[self.criticizeIndex()].pattern;
                }

                self.load("POST", data, function(error){
                    if(error){
                        self.isRetry(true);
                        self.guide.confuse();
                        self.setSession(self.session_template.message,
                           {message: "Oops, server cause error.\nPlease try again."});
                    }
                });

            }else{
                if(self.guideMode == self.guide_mode.proposed){
                    var next = self.criticizeIndex() + 1;
                    if(next >= self.criticizeIndex().length){
                        next = 0;
                    }
                    self.criticizeIndex(next);
                    self.showGuide(self.guide_mode.proposed);
                }else{
                    self.ask();
                }
            }
        }

        /*
         * for widget
         */
        self.widgetPlay = function(){
            if(self.isPlaying()){
              self._widget.pause();
            }else{
              self._widget.play();
            }
            self.isPlaying(!self.isPlaying());
        }

        self.widgetMove = function(isNext){
            var index = self.trackIndex();
            if(isNext){
                index += 1;
            }else{
                index -= 1;
            }

            if(index >= self.tracks().length){
                index = 0;
            }else if(index < 0){
                index = self.tracks().length - 1;
            }

            self.trackIndex(index);
            self.widgetLoadByIndex();
        }

        self.widgetLoadByIndex = function(index){
            var track = null;
            if(index){
                track = self.tracks()[index];
                self.trackIndex(index);
            }else{
                track = self.tracks()[self.trackIndex()];
            }
            /*
            var indexOfTrackInfo = -1;
            for(var i = 0; i < self.session().length;i++){
                if(self.session()[i].template == self.session_template.track){
                    indexOfTrackInfo = i;
                    break;
                }
            }

            if(indexOfTrackInfo > -1){
                self.session.splice(indexOfTrackInfo, 1);
            }*/
            self.showGuide(self.guide_mode.track);
            self.widgetLoad(track.permalink_url, self.isPlaying());

        }

        self.widgetLoad = function(url, isAutoLoad){
            if(self._widget == null){
                self._widget = initWidget(url);
                self._widget.bind(SC.Widget.Events["PLAY"],function(){
                    self.isPlaying(true);
                })
                self._widget.bind(SC.Widget.Events["PAUSE"],function(){
                    self.isPlaying(false);
                })

            }

            if(isAutoLoad){
                self._widget.load(url, {auto_play:true});
            }else{
                self._widget.load(url);
            }
        }
    }
    _vm = new mwViewModel();
    ko.applyBindings(_vm);
    _vm.init();

})