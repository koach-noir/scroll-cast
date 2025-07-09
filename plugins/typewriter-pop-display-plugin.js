/*
 * ScrollCast TypewriterPop Display Plugin
 * typewriter_pop アニメーション表示プラグイン
 */

window.TypewriterPopDisplayPlugin = {
    name: 'typewriter_pop_display',
    
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
            line.style.display = 'none';
            line.style.opacity = '0';
            line.style.transform = 'translate(-50%, -50%)';
        });
    },
    
    playSequence: function(sequenceIndex, sequenceData) {
        if (sequenceIndex >= this.lines.length) return;
        
        const line = this.lines[sequenceIndex];
        if (!line) return;
        
        this.animateTemplateLine(line, sequenceData);
    },
    
    animateTemplateLine: function(line, sequenceData) {
        // データ構造の互換性を保つ
        const duration = sequenceData.duration || sequenceData.total_duration || 8000;
        const durationMs = duration > 100 ? duration : duration * 1000;
        
        // 弾けて表示するアニメーション効果
        const bouncePhase = durationMs * 0.3;    // 30%: バウンス効果
        const holdPhase = durationMs * 0.5;      // 50%: 保持時間
        const fadePhase = durationMs * 0.2;      // 20%: フェードアウト
        
        // 初期状態: 非表示、スケール0
        line.style.display = 'block';
        line.style.opacity = '1';
        line.style.transform = 'translate(-50%, -50%) scale(0)';
        line.style.transition = 'none';
        
        // フェーズ1: バウンス効果 (0-30%)
        setTimeout(() => {
            line.style.transition = `transform ${bouncePhase / 3000}s cubic-bezier(0.68, -0.55, 0.265, 1.55)`;
            line.style.transform = 'translate(-50%, -50%) scale(1.2)';
            
            // フェーズ2: 少し縮小 (10-20%)
            setTimeout(() => {
                line.style.transition = `transform ${bouncePhase / 3000}s ease-out`;
                line.style.transform = 'translate(-50%, -50%) scale(0.9)';
                
                // フェーズ3: 通常サイズに収束 (20-30%)
                setTimeout(() => {
                    line.style.transition = `transform ${bouncePhase / 3000}s ease-out`;
                    line.style.transform = 'translate(-50%, -50%) scale(1)';
                    
                    // フェーズ4: 保持時間後にフェードアウト (80-100%)
                    setTimeout(() => {
                        line.style.transition = `opacity ${fadePhase}ms ease-in`;
                        line.style.opacity = '0';
                        
                        // アニメーション完了後のクリーンアップ
                        setTimeout(() => {
                            line.style.display = 'none';
                            line.style.transition = '';
                            line.style.transform = 'translate(-50%, -50%)';
                            line.style.opacity = '1';
                        }, fadePhase);
                    }, holdPhase);
                }, bouncePhase / 3);
            }, bouncePhase / 3);
        }, 50);
    }
};
