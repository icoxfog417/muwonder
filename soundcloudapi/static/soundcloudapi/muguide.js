var MuGuide = (function () {
    function MuGuide(canvasId) {
        this.canvasId = canvasId;
        this.canvas = document.getElementById(canvasId);
        this.context = this.canvas.getContext('2d');
        this.interval = null;
        this.state = "";
        this.bodyColor = "slategray";
    }

    MuGuide.State = {
        default:"default",
        waiting:"waiting",
        thinking:"thinking",
        listening:"listening",
        confusing:"confusing",
        sleeping:"sleeping",
        amazing:"amazing"
    }

    MuGuide.prototype.currentState = function () {
        return this.state;
    }

    MuGuide.prototype.default = function () {
        this.state = MuGuide.State.default;
        this.drawBody();
        this.drawMouth();
        this.drawEye(40,40,10);
        this.drawEye(80,40,10);
    };

    MuGuide.prototype.initialize = function () {
        this.clear(true);
        this.default();
    }

    MuGuide.prototype.waiting = function (isBegin) {
        if(isBegin){
            this.state = MuGuide.State.waiting;
            var self = this;
            this.default();
            clearInterval(this.interval);
            this.interval = setInterval(function(){
                self.clear();
                self.drawBody();
                self.drawMouth();
                self.drawEyeClose();
                setTimeout(function(){
                    self.default();
                },500);
            },4000);
        }else{
            this.initialize();
        }
    };

    MuGuide.prototype.thinking = function (isBegin) {
        if(isBegin){
            this.state = MuGuide.State.thinking;
            var totalCount = 0;
            var self = this;
            clearInterval(this.interval);
            this.interval = setInterval(function(){
                self.clear();
                self.drawBody();
                self.drawMothThink(totalCount);
                self.drawEyeClose();
                totalCount += 1;
            },500);
        }else{
            this.initialize();
        }
    };

    MuGuide.prototype.listening = function (isBegin) {
        if(isBegin){
            this.state = MuGuide.State.listening;
            var totalCount = 0;
            var self = this;
            clearInterval(this.interval);
            this.interval = setInterval(function(){
                self.clear();
                self.drawBody();
                if(totalCount % 2 == 0){
                    self.drawEye(40,30,10);
                    self.drawEye(80,30,10);
                }else{
                    self.drawEye(40,40,10);
                    self.drawEye(80,40,10);
                }
                self.drawMouth();
                totalCount += 1;
            },500);
        }else{
            this.initialize();
        }
    };

    MuGuide.prototype.confusing = function () {
        this.state = MuGuide.State.confusing;
        this.clear(true);
        this.drawBody();
        this.drawMouth();
        this.drawEyeConfuse();
    };

    MuGuide.prototype.sleeping = function () {
        this.state = MuGuide.State.sleeping;
        this.clear(true);
        this.drawBody();
        this.drawMouthSleep();
        this.drawEyeClose();
    };

    MuGuide.prototype.amazing = function () {
        this.state = MuGuide.State.amazing;
        this.clear(true);
        this.drawBody("coral");
        this.drawMouthAmazing();
        this.drawEye(40,40,15);
        this.drawEye(80,40,5);
    };

    MuGuide.prototype.drawBody = function (bodyColor) {
        this.context.beginPath();
        if(bodyColor !== undefined){
            this.context.fillStyle = bodyColor;
        }else{
            this.context.fillStyle = this.bodyColor;
        }
        this.context.fillRect(10,10,100,100);
    };

    MuGuide.prototype.drawEye = function(left,top, radius){
        this.context.beginPath();
        this.context.arc(left,top,radius,0,Math.PI*2,true);
        this.context.fillStyle = "white";
        this.context.fill();
    }

    MuGuide.prototype.drawEyeClose = function(){
        this.context.beginPath();
        this.context.fillStyle = "white";
        /*
        this.context.fillRect(30,40,5,5);
        this.context.fillRect(70,40,5,5);
        */
        this.context.fillRect(30,45,20,5);
        this.context.fillRect(70,45,20,5);

        this.context.fill();
    }

    MuGuide.prototype.drawEyeConfuse = function(){
        this.context.beginPath();
        this.context.fillStyle = "white";
        this.context.fillRect(20,30,30,10);
        this.context.fillRect(30,20,10,30);
        this.context.fillRect(70,30,30,10);
        this.context.fillRect(80,20,10,30);

        this.context.fill();
    }

    MuGuide.prototype.drawMouth = function(){
        this.context.beginPath();
        this.context.strokeStyle = "white";
        this.context.moveTo(20, 85);
        this.context.lineTo(40, 70);
        this.context.lineTo(60, 85);
        this.context.lineTo(80, 70);
        this.context.lineTo(100, 85);
        this.context.stroke();
    }

    MuGuide.prototype.drawMouthSleep = function(){
        this.context.beginPath();
        this.context.strokeStyle = "white";
        this.context.moveTo(30, 85);
        this.context.lineTo(90, 85);
        this.context.stroke();
    }

    MuGuide.prototype.drawMouthAmazing = function(){
        this.context.beginPath();
        this.context.strokeStyle = "white";
        this.context.arcTo(20, 85, 40, 70, 10);
        this.context.arcTo(40, 70, 60, 85, 10);
        this.context.arcTo(60, 85, 80, 70, 10);
        this.context.arcTo(80, 70, 100, 85, 10);
        this.context.arcTo(100, 85, 100, 85, 10);
        this.context.stroke();
    }

    MuGuide.prototype.drawMothThink = function(count){
        var sleepCount = count % 3;
        this.context.beginPath();
        this.context.fillStyle = "white";
        for(var i = 0; i <= sleepCount; i++){
            var index = i + 1;
            this.context.arc(20 + 20 * index,85,3,0,Math.PI*2,true);
            this.context.fill();
        }
    }


    MuGuide.prototype.clear = function(withInterval){
        if(withInterval !== undefined){
            clearInterval(this.interval);
        }
        this.context.clearRect(0,0,this.canvas.width,this.canvas.height);
    }

    return MuGuide;

})();