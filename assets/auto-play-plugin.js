/*
 * ScrollCast Auto Play Plugin
 * 自動再生機能プラグイン
 */

window.AutoPlayPlugin = {
    name: 'auto_play',
    
    initialize: function(config) {
        this.config = config;
        this.state = {
            isPlaying: false,
            globalTime: 0,
            startTime: null
        };
        this.timeline = [];
        this.setupTimeline();
        this.setupAutoPlay();
    },
    
    setupTimeline: function() {
        if (!this.config.timingData) return;
        
        this.config.timingData.forEach((sequenceData, index) => {
            const startTime = sequenceData.start_time || 0;
            
            this.timeline.push({
                time: startTime,
                type: 'sequence_start',
                index: index,
                data: sequenceData
            });
        });
        
        this.timeline.sort((a, b) => a.time - b.time);
    },
    
    setupAutoPlay: function() {
        const initialDelay = this.config.initial_delay || 1000;
        
        if (this.config.auto_start) {
            setTimeout(() => {
                this.startPlayback();
            }, initialDelay);
        }
        
        document.addEventListener('click', () => {
            if (this.state.isPlaying) {
                this.pausePlayback();
            } else {
                this.startPlayback();
            }
        });
    },
    
    startPlayback: function() {
        if (this.state.isPlaying) return;
        
        this.state.isPlaying = true;
        this.state.startTime = Date.now() - this.state.globalTime;
        this.updateLoop();
    },
    
    pausePlayback: function() {
        this.state.isPlaying = false;
    },
    
    updateLoop: function() {
        if (!this.state.isPlaying) return;
        
        this.state.globalTime = Date.now() - this.state.startTime;
        
        this.timeline.forEach(event => {
            if (event.time <= this.state.globalTime && !event.triggered) {
                event.triggered = true;
                window.dispatchEvent(new CustomEvent(event.type, {
                    detail: { index: event.index, data: event.data }
                }));
            }
        });
        
        requestAnimationFrame(() => this.updateLoop());
    }
};
