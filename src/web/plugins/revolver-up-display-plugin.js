/*
 * ScrollCast Revolver Up Display Plugin
 * リボルバーアップ表示プラグイン：左寄せ、中央行拡大、スライドアニメーション
 */

window.RevolverUpDisplayPlugin = {
    name: 'revolver_up_display',
    
    initialize: function(config) {
        this.config = config;
        this.container = document.querySelector('.text-container[data-template="revolver_up"]');
        this.viewport = document.querySelector('.revolver-viewport');
        this.lines = document.querySelectorAll('.text-line');
        this.currentLineIndex = 0;
        this.isAnimating = false;
        
        this.setupDisplayHandlers();
        this.initializeDisplay();
    },
    
    setupDisplayHandlers: function() {
        window.addEventListener('sequence_start', (event) => {
            this.playSequence(event.detail.index, event.detail.data);
        });
    },
    
    initializeDisplay: function() {
        // 全ての行を非表示にし、最初の数行のみ表示
        this.lines.forEach((line, index) => {
            line.style.opacity = '0.7';
            line.classList.remove('current');
            
            // 最初は3行まで表示（前後のコンテキスト）
            if (index < 3) {
                line.style.display = 'block';
            } else {
                line.style.display = 'none';
            }
        });
        
        // 最初の行をカレント行に設定
        if (this.lines.length > 0) {
            this.lines[0].classList.add('current');
            this.lines[0].style.opacity = '1';
        }
    },
    
    playSequence: function(sequenceIndex, sequenceData) {
        if (this.isAnimating || sequenceIndex >= this.lines.length) return;
        
        this.currentLineIndex = sequenceIndex;
        const currentLine = this.lines[this.currentLineIndex];
        if (!currentLine) return;
        
        this.animateRevolverUp(currentLine, sequenceData, sequenceIndex);
    },
    
    animateRevolverUp: function(line, sequenceData, sequenceIndex) {
        this.isAnimating = true;
        
        // カレント行設定
        this.updateCurrentLine(sequenceIndex);
        
        // 文字数に基づく待機時間（0.3秒/文字）
        const charCount = sequenceData.char_count || line.textContent.length;
        const displayDuration = Math.max(charCount * 300, 2000); // 最低2秒
        
        // 表示時間後にスライドアニメーション
        setTimeout(() => {
            this.slideToNextLine(sequenceIndex);
        }, displayDuration);
    },
    
    updateCurrentLine: function(lineIndex) {
        // 全ての行からcurrentクラスを削除
        this.lines.forEach(line => {
            line.classList.remove('current');
            line.style.opacity = '0.7';
        });
        
        // 新しいカレント行を設定
        if (this.lines[lineIndex]) {
            this.lines[lineIndex].classList.add('current');
            this.lines[lineIndex].style.opacity = '1';
        }
        
        // 表示範囲の調整（カレント行の前後を表示）
        this.updateVisibleLines(lineIndex);
    },
    
    updateVisibleLines: function(centerIndex) {
        const visibleRange = 3; // 前後何行まで表示するか
        
        this.lines.forEach((line, index) => {
            if (index >= centerIndex - visibleRange && index <= centerIndex + visibleRange) {
                line.style.display = 'block';
            } else {
                line.style.display = 'none';
            }
        });
    },
    
    slideToNextLine: function(currentIndex) {
        const nextIndex = currentIndex + 1;
        
        if (nextIndex >= this.lines.length) {
            // 最後の行に到達
            this.isAnimating = false;
            return;
        }
        
        // 全体を上にスライド（視覚的効果）
        this.lines.forEach(line => {
            line.style.transition = 'transform 0.8s ease-in-out';
            line.style.transform = 'translateY(-2rem)';
        });
        
        // スライドアニメーション完了後に次の行を準備
        setTimeout(() => {
            // 次の行の準備
            this.updateCurrentLine(nextIndex);
            this.updateVisibleLines(nextIndex);
            
            // 変形をリセット
            this.lines.forEach(line => {
                line.style.transform = 'translateY(0)';
                line.style.transition = '';
            });
            
            this.isAnimating = false;
        }, 800); // スライドアニメーション時間
    }
};