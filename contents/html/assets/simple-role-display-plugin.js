/*
 * ScrollCast Simple Role Display Plugin  
 * シンプルロール（エンドロール風）表示プラグイン
 */

window.SimpleRoleDisplayPlugin = {
    name: 'simple_role_display',
    
    initialize: function(config) {
        this.config = config;
        this.lines = document.querySelectorAll('.text-line');
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
            line.style.opacity = '0';
            line.style.transform = 'translateY(100vh)';
        });
    },
    
    playSequence: function(sequenceIndex, sequenceData) {
        if (sequenceIndex >= this.lines.length) return;
        
        const line = this.lines[sequenceIndex];
        if (!line) return;
        
        this.animateScrollLine(line, sequenceData);
    },
    
    animateScrollLine: function(line, sequenceData) {
        const duration = sequenceData.duration || 3000;
        
        line.animate([
            { opacity: 0, transform: 'translateY(100vh)' },
            { opacity: 1, transform: 'translateY(0)' },
            { opacity: 0, transform: 'translateY(-100vh)' }
        ], {
            duration: duration,
            easing: 'ease-in-out',
            fill: 'forwards'
        });
    }
};
