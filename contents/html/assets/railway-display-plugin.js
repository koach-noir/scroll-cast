/*
 * ScrollCast Railway Display Plugin
 * 鉄道方向幕風表示プラグイン
 */

window.RailwayDisplayPlugin = {
    name: 'railway_display',
    
    initialize: function(config) {
        this.config = config;
        this.lines = document.querySelectorAll('.text-line');
        this.currentLineIndex = 0;
        this.activeAnimations = new Map();
        this.setupDisplayHandlers();
        this.initializeDisplay();
    },
    
    setupDisplayHandlers: function() {
        window.addEventListener('sequence_start', (event) => {
            this.playSequence(event.detail.index, event.detail.data);
        });
    },
    
    initializeDisplay: function() {
        this.lines.forEach(line => {
            line.className = 'text-line';
            line.style.transform = 'translate(-50%, -50%) translateY(100px)';
            line.style.opacity = '0';
        });
    },
    
    playSequence: function(sequenceIndex, sequenceData) {
        if (sequenceIndex >= this.lines.length) return;
        
        this.currentLineIndex = sequenceIndex;
        const currentLine = this.lines[this.currentLineIndex];
        if (!currentLine) return;
        
        this.animateRailwayLineWithWebAPI(currentLine, sequenceData, sequenceIndex);
    },
    
    animateRailwayLineWithWebAPI: function(line, sequenceData, sequenceIndex) {
        const phases = this.createRailwayAnimationPhases(line, sequenceData, sequenceIndex);
        
        phases.forEach(phase => {
            const animation = line.animate(phase.keyframes, phase.options);
            
            animation.addEventListener('finish', () => {
                if (phase.onFinish) {
                    phase.onFinish(line);
                }
            });
        });
    },
    
    createRailwayAnimationPhases: function(line, sequenceData, sequenceIndex) {
        const fadeInDuration = sequenceData.fade_in_duration || 800;
        const staticDuration = sequenceData.static_duration || 2000;
        const fadeOutDuration = sequenceData.fade_out_duration || 800;
        const fadeInStart = sequenceData.fade_in_start || 0;
        const staticStart = sequenceData.static_start || fadeInDuration;
        const fadeOutStart = sequenceData.fade_out_start || (staticStart + staticDuration);
        
        return [
            {
                name: 'fade-in',
                keyframes: [
                    { opacity: 0, transform: 'translate(-50%, -50%) translateY(100px)', offset: 0 },
                    { opacity: 1, transform: 'translate(-50%, -50%) translateY(0px)', offset: 1 }
                ],
                options: { duration: fadeInDuration, delay: fadeInStart, fill: 'forwards', easing: 'ease-in-out' },
                onFinish: (line) => {
                    line.style.opacity = '1';
                    line.style.transform = 'translate(-50%, -50%) translateY(0px)';
                }
            },
            {
                name: 'static',
                keyframes: [
                    { opacity: 1, transform: 'translate(-50%, -50%) translateY(0px)', offset: 0 },
                    { opacity: 1, transform: 'translate(-50%, -50%) translateY(0px)', offset: 1 }
                ],
                options: { duration: staticDuration, delay: staticStart, fill: 'forwards', easing: 'linear' }
            },
            {
                name: 'fade-out',
                keyframes: [
                    { opacity: 1, transform: 'translate(-50%, -50%) translateY(0px)', offset: 0 },
                    { opacity: 0, transform: 'translate(-50%, -50%) translateY(-100px)', offset: 1 }
                ],
                options: { duration: fadeOutDuration, delay: fadeOutStart, fill: 'forwards', easing: 'ease-in-out' },
                onFinish: (line) => {
                    line.style.opacity = '0';
                    line.style.transform = 'translate(-50%, -50%) translateY(100px)';
                    line.className = 'text-line';
                }
            }
        ];
    }
};
