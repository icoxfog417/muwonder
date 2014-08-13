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

    //adjust content height to window size
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
        self.guide = new MuGuide("muguide");
        self.behaviorWatcher = new BehaviorWatcher();

        self.isPlaying = ko.observable(false);
        self.trackIndex = ko.observable(0);
        self.criticizeIndex = ko.observable(0);
        self.tracks = ko.observableArray([]);
        self.criticize = ko.observableArray([]);
        self.session = ko.observableArray([]);

        self.guideMode = 0;
        self.isRetry = ko.observable(false);
        self.errorStatus = "";

        self.session_template = {
            track : "track-template",
            message : "message-template",
            criticize : "criticize-template"
        }
        self.criticize_type = {
            pattern : 0,
            parameter : 1,
            like : 2
        }
        self.guide_mode = {
            pattern : 0,
            parameter : 1,
            like : 2,
            track : 8,
            reload : 9
        }
        self.askSequence = [self.guide_mode.track, self.guide_mode.reload, self.guide_mode.like, self.guide_mode.pattern];
        self.behaviorKind = {
            askAboutTrack : "askAboutTrack",
            askBPM : "askBPM"
        }

        /*
         * show conversation
         */
        self.addSession = function(template, data){
            var passData = data;
            if(passData["option"] === undefined){
                passData["option"] = null;
            }
            var s = {template:template, data:passData};
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
            //set timeline event
            self.behaviorWatcher.subscribe(self.behaviorKind.askAboutTrack,30000,function(){
                 self.showGuide(self.guide_mode.like);
                 return true;
            })

            //set ask bpm event
            self.behaviorWatcher.subscribe(self.behaviorKind.askBPM,2000,function(detectCount, elapsed){
                bpm = Math.floor((detectCount / elapsed) * 1000 * 60);
                if(bpm > 50){
                    self.guide.amazing();
                    var option = {
                        parameter: bpm
                    };
                    self.showGuide(self.guide_mode.parameter, option);
                    return true;
                }
            })

            //set timeline event
            self.behaviorWatcher.subscribeNoBehaviorHandler(30000,function(){
                self.showGuide(self.guide_mode.reload);
                return true;
            })

            //for Django csrf
            $.ajaxSetup({
                beforeSend: function(xhr, settings) {
                    if (!(/^(GET|HEAD|OPTIONS|TRACE)$/.test(settings.type)) && !this.crossDomain) {
                        var csrftoken = $.cookie('csrftoken');
                        xhr.setRequestHeader("X-CSRFToken", csrftoken);
                    }
                }
            });

            self.behaviorWatcher.start();
            self.getTracks("Let me introduce you the various genre tracks!");
        }

        self.getTracks = function(message){
            self.setSession(self.session_template.message, {message: message});
            self.guide.thinking(true);

            self.load("GET", {}, function(error){
                if(!error){
                    self.guide.waiting(true);
                    self.widgetLoadByIndex(0);
                }else{
                    self.guide.confusing();
                    self.isRetry(true);
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
                    playing = self.tracks()[self.trackIndex()];
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
            self.getTracks("Try again ...");
        }

        /*
         * for criticize
         */
        self.ask = function(){
            if(self.guideMode != self.guide_mode.parameter){
                self.guide.waiting();
                var nextIndex = self.askSequence.indexOf(self.guideMode) + 1;
                var nextIndex = nextIndex % self.askSequence.length;
                self.showGuide(self.askSequence[nextIndex]);
                self.behaviorWatcher.detect(self.behaviorKind.askBPM);
            }
        }

        self.showGuide = function(mode, option){
            var isModeUpdate = true;

            if(mode == self.guide_mode.pattern && self.criticize().length > 0){
                self.setSession(self.session_template.criticize, self.criticize()[self.criticizeIndex()]);
            }else if(mode == self.guide_mode.parameter){
                self.setSession(self.session_template.criticize, {text: "Oh, do you like this " + option.parameter + " beat!?", option:option});
            }else if(mode == self.guide_mode.like && self.tracks().length > 0){
                self.setSession(self.session_template.criticize, {text: "Do you like this Track?"});
            }else if(mode == self.guide_mode.track && self.tracks().length > 0){
                self.setSession(self.session_template.track, self.tracks()[self.trackIndex()]);
            }else if(mode == self.guide_mode.reload){
                self.setSession(self.session_template.criticize, {text: "Shall I show another tracks?"});
            }else{
                isModeUpdate = false;
            }

            if(isModeUpdate){
                self.guideMode = mode;
            }
        }

        self.answer = function(answer, option){
            if(answer){
                var data = {
                    track_id: self.tracks()[self.trackIndex()].id
                };

                switch(self.guideMode){
                    case self.guide_mode.like:
                        data.criticize_type = self.criticize_type.like;
                        self.doCriticize(data);
                        break;
                    case self.guide_mode.pattern:
                        data.criticize_type = self.criticize_type.pattern;
                        data.value = self.criticize()[self.criticizeIndex()].pattern;
                        self.doCriticize(data);
                        break;
                    case self.guide_mode.parameter:
                        data.criticize_type = self.criticize_type.parameter;
                        data.value = option.parameter;
                        self.doCriticize(data);
                        break;
                    case self.guide_mode.reload:
                        self.getTracks("Ok, I show new tracks that you will like.");
                }

            }else{
                switch(self.guideMode){
                    case self.guide_mode.pattern:
                        var next = self.criticizeIndex() + 1;
                        if(next >= self.criticizeIndex().length){
                            next = 0;
                        }
                        self.criticizeIndex(next);
                        self.showGuide(self.guide_mode.pattern);
                        break;
                    default:
                        self.guide.waiting(true);
                        self.setSession(self.session_template.message,
                            {message: "OK. Please ask me whenever you need."});
                        setTimeout(function(){
                            self.showGuide(self.guide_mode.track);
                        }, 2000);
                        break;
                }
            }
        }

        self.doCriticize = function(data){
            self.setSession(self.session_template.message,
               {message: "Ok, I show new tracks that you will like."});
            self.guide.thinking(true);

            self.load("POST", data, function(error){
                if(!error){
                    self.guide.waiting(true);
                    self.setSession(self.session_template.message,
                       {message: "Here the tracks, please listen to it."});
                }else{
                    self.isRetry(true);
                    self.guide.confusing();
                    self.setSession(self.session_template.message,
                       {message: "Oops, server cause error.\nPlease try again."});
                }
            });
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

        self.widgetRepeat = function(){
            self._widget.seekTo(0);
            self._widget.play();
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

            self.behaviorWatcher.resetHandler(self.behaviorKind.askAboutTrack, 0);
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
                    self.behaviorWatcher.resetHandler(self.behaviorKind.askAboutTrack, 0);
                    self.isPlaying(true);
                })
                self._widget.bind(SC.Widget.Events["PAUSE"],function(){
                    self.isPlaying(false);
                    self.behaviorWatcher.resetHandler(self.behaviorKind.askAboutTrack, 0);
                })
                self._widget.bind(SC.Widget.Events["PLAY_PROGRESS"],function(){
                    var pos = self._widget.getPosition();
                    self._widget.getPosition(function(value){
                        if(value < 30000){
                            self.behaviorWatcher.detect(self.behaviorKind.askAboutTrack);
                        }
                    })
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