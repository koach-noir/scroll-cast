/*
 * ScrollCast TypewriterFillScreen Display Plugin
 * typewriter_fill_screen アニメーション表示プラグイン
 */

window.TypewriterFillScreenDisplayPlugin = {
    name: 'typewriter_fill_screen_display',
    
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
        
        // 画面サイズと行間隔の計算
        const fontSize = 64; // デフォルトフォントサイズ
        const lineHeight = fontSize * 1.2;
        const screenHeight = window.innerHeight;
        const linesPerScreen = Math.floor(screenHeight / lineHeight);
        
        // 現在の行インデックスを取得（ライン要素から）
        const lineIndex = Array.from(this.lines).indexOf(line);
        const linePositionInScreen = lineIndex % linesPerScreen;
        const screenNumber = Math.floor(lineIndex / linesPerScreen);
        
        // Y座標計算（上端から下端まで敷き詰め）
        const yPosition = (linePositionInScreen * lineHeight) + (fontSize / 2);
        
        // 画面クリア効果（新しい画面の最初の行の時）
        if (linePositionInScreen === 0 && screenNumber > 0) {
            this.clearScreen();
        }
        
        // 初期状態を設定（画面上の固定位置）
        line.style.display = 'block';
        line.style.opacity = '0';
        line.style.position = 'absolute';
        line.style.left = '50%';
        line.style.top = `${yPosition}px`;
        line.style.transform = 'translateX(-50%)';
        line.style.fontSize = `${fontSize}px`;
        line.style.color = 'white';
        line.style.textAlign = 'center';
        line.style.zIndex = '1';
        
        // フェードイン効果
        setTimeout(() => {
            line.style.transition = 'opacity 0.2s ease-in';
            line.style.opacity = '1';
            
            // 表示時間後にフェードアウト
            setTimeout(() => {
                line.style.transition = 'opacity 0.2s ease-out';
                line.style.opacity = '0';
                
                // アニメーション完了後のクリーンアップ
                setTimeout(() => {
                    line.style.display = 'none';
                    line.style.transition = '';
                    line.style.position = '';
                    line.style.left = '';
                    line.style.top = '';
                    line.style.transform = '';
                    line.style.fontSize = '';
                    line.style.color = '';
                    line.style.textAlign = '';
                    line.style.zIndex = '';
                }, 200);
            }, durationMs - 400);
        }, 50);
    },
    
    clearScreen: function() {
        // 画面上の全てのテキストを一時的にクリア
        this.lines.forEach(line => {
            if (line.style.display === 'block') {
                line.style.transition = 'opacity 0.1s ease-out';
                line.style.opacity = '0';
                setTimeout(() => {
                    line.style.display = 'none';
                }, 100);
            }
        });
    }
};
