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
        const duration = sequenceData.duration || 8000;
        
        line.style.display = 'block';
        line.style.position = 'fixed';
        line.style.left = '50%';
        line.style.top = '50%';
        line.style.zIndex = '100';
        line.style.transform = 'translate(-50%, -50%) translateY(100vh)';
        line.style.opacity = '1';
        
        // エンドロール風アニメーション開始
        setTimeout(() => {
            line.style.transition = 'transform 8s linear';
            line.style.transform = 'translate(-50%, -50%) translateY(-100vh)';
            
            // 画面を完全に通過した後に非表示
            setTimeout(() => {
                line.style.display = 'none';
                line.style.transition = '';
                line.style.transform = '';
            }, 8000);
        }, 50);
    }
};
