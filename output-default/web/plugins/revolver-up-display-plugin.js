/*
 * ScrollCast Revolver Up Display Plugin - 2024 Modern Implementation  
 * simple_roleベース + 中央通過時ハイライト効果
 */

window.RevolverUpDisplayPlugin = {
    name: 'revolver_up_display',
    
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
        
        this.animateRevolverLine(line, sequenceData);
    },
    
    animateRevolverLine: function(line, sequenceData) {
        // revolver_up timing data structure support
        const duration = sequenceData.total_duration || sequenceData.duration || 8000;
        const durationMs = duration > 100 ? duration : duration * 1000; // Handle both ms and seconds
        
        line.style.display = 'block';
        line.style.position = 'fixed';
        line.style.left = '50%';
        line.style.top = '50%';
        line.style.zIndex = '100';
        line.style.transform = 'translate(-50%, -50%) translateY(100vh) scale(1)';
        line.style.opacity = '1';
        line.style.color = '#fff';
        
        // simple_roleと同じ下→上スクロール + 中央通過時ハイライト
        setTimeout(() => {
            const transitionDuration = durationMs / 1000; // Convert to seconds for CSS
            line.style.transition = `transform ${transitionDuration}s linear, color 0.5s ease, text-shadow 0.5s ease`;
            line.style.transform = 'translate(-50%, -50%) translateY(-100vh) scale(1)';
            
            // 中央通過時（全体の25%-75%）にハイライト効果
            const highlightStart = durationMs * 0.25;
            const highlightEnd = durationMs * 0.75;
            
            setTimeout(() => {
                line.style.transform = 'translate(-50%, -50%) translateY(-20vh) scale(1.5)';
                line.style.color = '#ffff99';
                line.style.textShadow = '0 0 20px rgba(255, 255, 153, 0.8)';
            }, highlightStart);
            
            // ハイライト解除して通常スクロール継続
            setTimeout(() => {
                line.style.transform = 'translate(-50%, -50%) translateY(-100vh) scale(1)';
                line.style.color = '#fff';
                line.style.textShadow = 'none';
            }, highlightEnd);
            
            // 画面を完全に通過した後に非表示
            setTimeout(() => {
                line.style.display = 'none';
                line.style.transition = '';
                line.style.transform = '';
                line.style.color = '';
                line.style.textShadow = '';
            }, durationMs);
        }, 50);
    }
};