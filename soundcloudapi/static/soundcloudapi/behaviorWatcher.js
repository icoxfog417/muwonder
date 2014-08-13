var BehaviorWatcher = (function () {
    function BehaviorWatcher(intervalTime) {
        this.intervalTime = 333;
        if(intervalTime){
            this.intervalTime = intervalTime;
        }
        this.timer = null;
        this.handlers = {};
        this.__NO_BEHAVIOR_HANDLER_NAME = "NO_BEHAVIOR_HANDLER_NAME";
    }

    BehaviorWatcher.prototype.start = function () {
        var self = this;
        this.timer = setInterval(function(){
            var timeNow = new Date();
            var keys = [];
            for(var key in self.handlers){ keys.push(key); }
            var sortedKeys = [];
            var isNoBehaviorHandlerExist = false;

            //sort handlers (move no behavior function to back)
            for(var i = 0; i < keys.length; i++){
                if(keys[i] != self.__NO_BEHAVIOR_HANDLER_NAME){
                    sortedKeys.push(keys[i]);
                }else{
                    isNoBehaviorHandlerExist = true;
                }
            }
            if(isNoBehaviorHandlerExist){
                sortedKeys.push(self.__NO_BEHAVIOR_HANDLER_NAME);
            }

            //evaluate each handler
            for(var i = 0; i < sortedKeys.length; i++){
                key = sortedKeys[i];
                var h = self.handlers[key];
                if(h.startTime == null){
                    h.startTime = new Date();
                }
                var elapsed = timeNow - h.startTime;
                if(elapsed > h.handler.boundarySeconds){
                    var isContinue = true;
                    if(h.detectedCount > 0){
                        isContinue = h.handler.callback(h.detectedCount, elapsed);
                        if(key != self.__NO_BEHAVIOR_HANDLER_NAME){
                            self.detect(self.__NO_BEHAVIOR_HANDLER_NAME, 0);
                        }
                    }else{
                        if(key != self.__NO_BEHAVIOR_HANDLER_NAME){
                            self.detect(self.__NO_BEHAVIOR_HANDLER_NAME);
                        }
                    }

                    if(!isContinue){
                        self.unsubscribe(h.handler.name);
                    }else{
                        h.detectedCount = 0;
                        h.startTime = new Date();
                    }
                }else if(key != self.__NO_BEHAVIOR_HANDLER_NAME && h.detectedCount > 0){
                    //some detect occured, reset no behavior
                    self.detect(self.__NO_BEHAVIOR_HANDLER_NAME, 0);
                }
            }

        }, self.intervalTime);
    };

    BehaviorWatcher.prototype.stop = function () {
        clearInterval(this.timer);
    };

    BehaviorWatcher.prototype.createBehaviorHandler = function (name, boundarySeconds, callback) {
        //name: the name of behavior
        //boundarySeconds: the boundary to judge behavior is occured
        //callback: the function that invoked when behavior is occured
        return {
            name: name,
            boundarySeconds: boundarySeconds,
            callback: callback
        };
    };

    BehaviorWatcher.prototype.subscribe = function (name, boundarySeconds, callback) {
        var handler = this.createBehaviorHandler(name, boundarySeconds, callback);
        var watcherObj = {
            detectedCount: 0,
            handler: handler,
            startTime: null
        };

        if(handler.name in this.handlers){
            throw "Handler" + handler.name + " is already subscribed";
        }else{
            this.handlers[handler.name] = watcherObj;
        }
    };

    BehaviorWatcher.prototype.unsubscribe = function (name) {
        if(name in this.handlers){
            delete this.handlers[name];
        }
    };

    BehaviorWatcher.prototype.detect = function (name, value) {
        if(name in this.handlers){
            if(value !== undefined){
                this.handlers[name].detectedCount = value;
            }else{
                this.handlers[name].detectedCount += 1;
            }
        }
    };

    BehaviorWatcher.prototype.resetHandler = function (name) {
        if(name in this.handlers){
            this.handlers[name].detectedCount = 0;
            this.handlers[name].startTime = new Date();
        }
    };

    BehaviorWatcher.prototype.subscribeNoBehaviorHandler = function (boundarySeconds, callback) {
        this.subscribe(this.__NO_BEHAVIOR_HANDLER_NAME, boundarySeconds, callback);
    };

    return BehaviorWatcher;

})();
