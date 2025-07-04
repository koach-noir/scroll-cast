// ============================================================================
// Scroll Base Library - Scroll系テンプレート共通機能
// ============================================================================

// ScrollCastBaseを継承
window.ScrollBase = Object.assign({}, window.ScrollCastBase, {
    name: 'scroll_base',
    
    // Scroll系共通初期化
    initialize: function(config) {
        console.log('[ScrollBase] Initializing with config:', config);
        this.initializeCommon(config);
        this.lineElements = document.querySelectorAll('.scroll-line');
        console.log(`[ScrollBase] Found ${this.lineElements.length} lines`);
        this.state = {
            currentLine: 0,
            isDisplaying: false
        };
        this.totalLines = this.lineElements.length;
        this.setupScrollEventHandlers();
        this.initializeScrollDisplay();
        console.log('[ScrollBase] Initialization complete');
    },
    
    // Scroll系共通イベントハンドラー
    setupScrollEventHandlers: function() {
        console.log('[ScrollBase] Setting up scroll event handlers');
        window.addEventListener('sequence_start', (event) => {
            console.log('[ScrollBase] Received sequence_start event:', event.detail);
            this.showLine(event.detail.index);
        });
    },
    
    // Scroll系共通表示初期化
    initializeScrollDisplay: function() {
        // 初期状態で全ての行を非表示
        this.lineElements.forEach(line => {
            line.style.display = 'none';
            this.resetLineToInitialPosition(line);
        });
        
        // コンテナの設定
        const container = document.querySelector('.scroll-container');
        if (container) {
            container.style.overflow = 'hidden';
            container.style.height = '100vh';
        }
    },
    
    // 行を初期位置にリセット（サブクラスでオーバーライド可能）
    resetLineToInitialPosition: function(line) {
        line.style.transform = 'translate(-50%, 100vh)';
        line.style.opacity = '1';
    },
    
    // 行の表示処理（サブクラスでオーバーライド）
    showLine: function(lineIndex) {
        console.log(`[ScrollBase] Base showLine called for index ${lineIndex} - should be overridden by subclass`);
        
        if (lineIndex < 0 || lineIndex >= this.totalLines) {
            console.log(`[ScrollBase] Index ${lineIndex} out of bounds`);
            return;
        }
        
        const currentLine = this.lineElements[lineIndex];
        if (currentLine) {
            console.log(`[ScrollBase] Showing line ${lineIndex}: "${currentLine.textContent}"`);
            
            // 基本的な表示処理
            this.prepareLineForDisplay(currentLine, lineIndex);
            this.animateLineDisplay(currentLine, lineIndex);
        } else {
            console.log(`[ScrollBase] No line found at index ${lineIndex}`);
        }
        
        this.state.currentLine = lineIndex;
    },
    
    // 行の表示準備
    prepareLineForDisplay: function(line, lineIndex) {
        // CSS初期状態制御を解除して表示可能にする
        line.classList.add('active');
        line.classList.add('animating');
        line.style.display = 'block';
        line.style.position = 'fixed';
        line.style.left = '50%';
        line.style.top = '0';
        line.style.zIndex = '100';
        line.style.whiteSpace = 'nowrap';
        line.style.fontSize = '3vw';
        line.style.color = '#ffffff';
        line.style.textShadow = '2px 2px 4px rgba(0, 0, 0, 0.8)';
        
        // 初期位置設定
        this.resetLineToInitialPosition(line);
        
        console.log(`[ScrollBase] Made line ${lineIndex} visible with active classes`);
    },
    
    // 行のアニメーション（サブクラスでオーバーライド）
    animateLineDisplay: function(line, lineIndex) {
        console.log(`[ScrollBase] Base animateLineDisplay - should be overridden by subclass`);
        
        // デフォルトの基本アニメーション
        setTimeout(() => {
            line.style.transition = 'transform 3s linear';
            line.style.transform = 'translate(-50%, -100vh)';
            
            setTimeout(() => {
                line.style.display = 'none';
                line.style.transition = '';
                line.style.transform = '';
            }, 3000);
        }, 50);
    },
    
    // スクロール設定の取得
    getScrollConfig: function(config) {
        return {
            duration: config.scroll_duration || 8000,
            easing: config.scroll_easing || 'linear',
            startDelay: config.start_delay || 50,
            fontSize: config.font_size || '3vw',
            fontSizeDesktop: config.font_size_desktop || '36px'
        };
    },
    
    // デスクトップ用フォントサイズ適用
    applyResponsiveFontSize: function(line, config) {
        const scrollConfig = this.getScrollConfig(config);
        line.style.fontSize = scrollConfig.fontSize;
        
        // デスクトップ対応
        if (window.innerWidth >= 768) {
            line.style.fontSize = scrollConfig.fontSizeDesktop;
        }
    },
    
    // 状態取得
    getState: function() {
        return {
            currentLine: this.state.currentLine,
            totalLines: this.totalLines,
            isDisplaying: this.state.isDisplaying
        };
    }
});