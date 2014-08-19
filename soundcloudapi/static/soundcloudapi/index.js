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
        self.trackInWidget = null;
        self.API_RECOMMEND = "/soundcloudapi/recommends/";
        self.API_GET_PATTERN = "/soundcloudapi/criticize_pattern/";
        self.guide = new MuGuide("muguide");
        self.behaviorWatcher = new BehaviorWatcher();

        self.tracks = ko.observableArray([]);
        self.liked = ko.observableArray([]);
        self.trackIndex = ko.observable(0);
        self.criticize = ko.observableArray([]);
        self.criticizeIndex = ko.observable(0);
        self.isPlaying = ko.observable(false);
        self.history = [];
        self.session = ko.observableArray([]);

        self.content_mode = {
            none : "none-template",
            track : "track-template",
            like : "like-template"
        }
        self.session_template = {
            message : "message-template",
            criticize : "criticize-template"
        }
        self.criticize_type = {
            pattern : 0,
            parameter : 1,
            like : 2
        }
        self.guide_mode = {
            none : -1,
            pattern : 0,
            parameter : 1,
            like : 2,
            message: 8,
            reload : 9,
            retry : 10
        }
        self.guideMode =ko.observable(self.guide_mode.none);
        self.contentMode =ko.observable(self.content_mode.none);
        self.listMode =ko.observable(self.content_mode.none);

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
                if(self.guideMode() == self.guide_mode.track){
                    self.showGuide(self.guide_mode.like);
                }
                return true;
            });

            //set ask bpm event
            self.behaviorWatcher.subscribe(self.behaviorKind.askBPM,2000,function(detectCount, elapsed){
                bpm = Math.floor((detectCount / elapsed) * 1000 * 60);
                if(bpm > 50){
                    self.guide.amazing();
                    var option = {
                        parameter: bpm
                    };
                    self.showGuide(self.guide_mode.parameter, option);
                }
                return true;
            });

            //set timeline event
            self.behaviorWatcher.subscribeNoBehaviorHandler(30000,function(){
                if(self.guideMode() == self.guide_mode.track){
                    self.showGuide(self.guide_mode.reload);
                }
                return true;
            });

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

        /*
            server access
         */
        self.getTracks = function(message, postData){
            self.showGuide(self.guide_mode.message, {message: message});
            self.guide.thinking(true);

            var success = function(tracks){
                if(tracks && tracks.length > 0){
                    self.listMode(self.content_mode.none);
                    self.contentMode(self.content_mode.none);
                    self.tracks.removeAll();
                    tracks.forEach(function(item){
                      self.tracks.push(item);
                    })

                    self.guide.waiting(true);
                    self.listMode(self.content_mode.track);
                    self.contentMode(self.content_mode.track);
                    self.widgetLoadByIndex(0);
                }
                self.guideMode(self.guide_mode.none);
            }

            var error = function(error){
                console.log(error);
                self.showGuide(self.guide_mode.retry, {message: "Oops, server cause error.\nPlease try again."});
            }

            if(postData === undefined){
                self.load(self.API_RECOMMEND,  "GET", {}, success, error);
            }else{
                self.load(self.API_RECOMMEND, "POST", postData, success, error);
            }

        }

        self.getPatterns = function(){
            var data = {"track_id": self.tracks()[self.trackIndex()].item.id};
            var success = function(patterns){
                            if(patterns && patterns.length > 0){
                                self.criticizeIndex(0)
                                self.criticize.removeAll();
                                patterns.forEach(function(item){
                                  self.criticize.push(item);
                                })
                            }
                          }
            var error = function(error){
                console.log(error);
                self.showGuide(self.guide_mode.retry, {message: "Oops, I couldn't get criticize patterns."});
            }

            self.load(self.API_GET_PATTERN, "POST", data, success, error);
        }

        self.load = function(target, method, data, success, error){
            self.history.push({target: target, method: method, data:data, success:success, error:error});
            if(self.history.length > 5){
                self.history.shift()
            }
            return $.ajax({
                type: method,
                data: data,
                url: target,
                dataType: "json",
                success: success,
                error: error
            })
        }

        /*
         * error handler
         */
        self.retry = function(){
            var errorOccured = self.errorStatus;
            var lastExecute = self.history[self.history.length - 1];
            self.load(lastExecute.target, lastExecute.method, lastExecute.data, lastExecute.success, lastExecute.error);
        }

        /*
         * for track display
        */
        self.getTrackList = function(){
            switch(self.listMode()){
                case self.content_mode.track:
                    return self.tracks;
                    break;
                case self.content_mode.like:
                    return self.liked;
                    break;
            }
            return function(){return [];};
        };
        self.observeTrackList = ko.computed(self.getTrackList);

        self.drawTrackGraph = function(){
            scores = self.tracks()[self.trackIndex()].score_detail;
            var ctx = $("#trackRaderChart").get(0).getContext("2d");
            var graphData = {
                labels: ["PlayBack", "Like", "Download", "Comments", "Recent"],
                datasets: [
                    {
                        label: "My First dataset",
                        fillColor: "rgba(220,220,220,0.2)",
                        strokeColor: "rgba(220,220,220,1)",
                        pointColor: "rgba(220,220,220,1)",
                        pointStrokeColor: "#fff",
                        pointHighlightFill: "#fff",
                        pointHighlightStroke: "rgba(220,220,220,1)",
                        data: [scores.playback_count, scores.favoritings_count, scores.download_count, scores.comment_count, scores.elapsed]
                    }
                ]
            }
            var chart = new Chart(ctx).Radar(graphData);
        }

        self.getBodyContent = ko.computed(function(){
            switch(self.contentMode()){
                case self.content_mode.track:
                    selected = self.getSelected();
                    if(selected !== undefined){
                        return { name: self.content_mode.track, data: selected, afterRender:self.drawTrackGraph }
                    }else{
                        return { name: self.content_mode.none };
                    }
                    break;
                case self.content_mode.like:
                    return { name: self.content_mode.like, data: self.liked() }
                    break;
            }
            return {};
        })

        self.toggleListMode = function(){
            var setToIndex = function(fromList, toList, index){
                if(index() < fromList().length && fromList()[index()] !== undefined){
                    var toIndex = self._getIndex(fromList()[index()].item.id, toList());
                    toIndex = toIndex > -1 ? toIndex : 0;
                    index(toIndex);
                }else{
                    index(0);
                }
            }

            switch(self.listMode()){
                case self.content_mode.track:
                    setToIndex(self.tracks, self.liked, self.trackIndex);
                    self.listMode(self.content_mode.like);
                    break;
                default:
                    setToIndex(self.liked, self.tracks, self.trackIndex);
                    self.listMode(self.content_mode.track);
                    break;
            }
        }

        self.toggleContentMode = function(){
            switch(self.contentMode()){
                case self.content_mode.track:
                    self.contentMode(self.content_mode.like);
                    break;
                default:
                    self.contentMode(self.content_mode.track);
                    break;
            }
        }

        self.getTrackIndex = function(trackId){
            return self._getIndex(trackId, self.tracks());
        }

        self.getLikedIndex = function(trackId){
            return self._getIndex(trackId, self.liked());
        }

        self.getSelected = function(){
            return self.getTrackList()()[self.trackIndex()];
        }

        self._getIndex = function(trackId, trackArray){
            var id = trackId;
            var trackIndex = -1;

            if(id === undefined || id == ""){
                id = self.getSelected().item.id;
            }

            for(var i = 0; i < trackArray.length;i++){
                if(trackArray[i].item.id == id){
                    trackIndex = i;
                    break;
                }
            }
            return trackIndex;
        }

        self.toggleLike = function(){
            var selected = self.getSelected();
            var trackIndex = -1;
            if(self.trackInWidget != null){
                selected = self.trackInWidget;
                trackIndex = self.getLikedIndex(selected.item.id);
            }else if(selected !== undefined){
                trackIndex = self.getLikedIndex(selected.item.id);
            }

            if(trackIndex < 0){
                self.liked.push(selected);
            }else{
                self.liked.splice(trackIndex, 1);
            }
        }

        self.trackStyle = function(index){
            var css = "track";
            if(index == self.trackIndex()){
                css += " active";
            }
            return css;
        }

        /*
         * for criticize
         */
        self.ask = function(){
            self.guide.waiting();
            var guideSequence = [self.guide_mode.pattern, self.guide_mode.none];
            if(self.getLikedIndex() > -1){
                guideSequence.unshift(self.guide_mode.like);
            }
            var guideNow = guideSequence.indexOf(self.guideMode());
            if(guideNow > -1){
                guideNext = (guideNow + 1) % guideSequence.length;
                self.showGuide(guideSequence[guideNext]);
            }else{
                self.showGuide(self.guide_mode.none);
            }
        }

        self.showGuide = function(mode, option){
            var isModeUpdate = true;

            if(mode == self.guide_mode.pattern && self.criticize().length > 0){
                self.setSession(self.session_template.criticize, self.criticize()[self.criticizeIndex()]);
            }else if(mode == self.guide_mode.parameter){
                self.setSession(self.session_template.criticize, {text: "Oh, do you like this " + option.parameter + " beat!?", option:option});
            }else if(mode == self.guide_mode.like){
                self.setSession(self.session_template.criticize, {text: "Would you like similar tracks?"});
            }else if(mode == self.guide_mode.message){
                self.setSession(self.session_template.message, option);
            }else if(mode == self.guide_mode.reload){
                self.setSession(self.session_template.criticize, {text: "Shall I show another tracks?"});
            }else if(mode == self.guide_mode.retry){
                self.guide.confusing();
                self.setSession(self.session_template.message, option);
            }else if(mode == self.guide_mode.none){
                //nothing
            }else{
                isModeUpdate = false;
            }

            if(isModeUpdate){
                self.guideMode(mode);
            }
        }

        self.answer = function(answer, option){
            var msg = "Ok, I show new tracks that you will like.";

            if(answer){
                var selected = self.getSelected();
                var data = {
                    track_id: selected.item.id
                };

                switch(self.guideMode()){
                    case self.guide_mode.like:
                        data.criticize_type = self.criticize_type.like;
                        self.getTracks(msg, data);
                        break;
                    case self.guide_mode.pattern:
                        data.criticize_type = self.criticize_type.pattern;
                        data.value = self.criticize()[self.criticizeIndex()].pattern;
                        self.getTracks(msg, data);
                        break;
                    case self.guide_mode.parameter:
                        data.criticize_type = self.criticize_type.parameter;
                        data.value = option.parameter;
                        self.getTracks(msg, data);
                        break;
                    case self.guide_mode.reload:
                        self.getTracks(msg);
                }

            }else{
                switch(self.guideMode()){
                    case self.guide_mode.pattern:
                        var next = self.criticizeIndex() + 1;
                        if(next < self.criticize().length){
                            self.criticizeIndex(next);
                            self.showGuide(self.guide_mode.pattern);
                        }else{
                            self.showGuide(self.guide_mode.reload);
                        }
                        break;
                    default:
                        self.ask();
                        break;
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

        self.widgetBackTop = function(){
            self._widget.seekTo(0, function(){
               self._widget.play();
            });
        }

        self.widgetMove = function(isNext){
            var index = self.trackIndex();
            if(isNext){
                index += 1;
            }else{
                index -= 1;
            }

            if(index >= self.getTrackList()().length){
                index = 0;
            }else if(index < 0){
                index = self.getTrackList()().length - 1;
            }

            self.behaviorWatcher.resetHandler(self.behaviorKind.askAboutTrack, 0);
            self.trackIndex(index);
            self.widgetLoadByIndex();
        }

        self.widgetLoadByIndex = function(index){
            var track = null;
            if(index > -1){
                track = self.getTrackList()()[index];
                self.trackIndex(index);
            }else{
                track = self.getSelected();
            }
            self.widgetLoad(track, self.isPlaying());
            self.getPatterns();
        }

        self.widgetLoad = function(track, isAutoLoad){
            var url = track.item.permalink_url;
            self.trackInWidget = track;
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