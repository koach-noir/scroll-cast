// ============================================================================
// Scroll Role Plugin - エンドロール風スクロール効果
// ============================================================================

// ScrollBaseを継承
window.ScrollRolePlugin = Object.assign({}, window.ScrollBase, {
    name: 'scroll_role',
    
    // エンドロール効果固有の初期化
    initialize: function(config) {
        console.log('[ScrollRole] Initializing role-specific features');
        // 基底クラスの初期化を呼び出し
        window.ScrollBase.initialize.call(this, config);
        
        // エンドロール効果固有の設定
        this.roleConfig = {
            // 基本設定
            scrollDuration: config.scroll_duration || 8000,
            scrollEasing: config.scroll_easing || 'linear',
            // アニメーション設定（互換性のため）
            duration: config.scroll_duration || 8000,
            easing: config.scroll_easing || 'linear',
            startDelay: config.start_delay || 50,
            // エンドロール固有の設定
            continuousDisplay: config.continuous_display !== false, // デフォルトは連続表示
            lineSpacing: config.line_spacing || 200, // 行間のタイミング
            fadeEffect: config.fade_effect !== false // デフォルトはフェード効果あり
        };
        
        console.log('[ScrollRole] Role configuration:', this.roleConfig);
    },
    
    // 行の表示処理（エンドロール効果）をオーバーライド
    showLine: function(lineIndex) {
        if (lineIndex < 0 || lineIndex >= this.totalLines) {
            console.log(`[ScrollRole] Index ${lineIndex} out of bounds`);
            return;
        }
        
        console.log(`[ScrollRole] Showing line ${lineIndex}:`, this.lineElements[lineIndex]?.textContent);
        
        const currentLine = this.lineElements[lineIndex];
        if (currentLine) {
            // エンドロール用の行準備
            this.prepareRoleLineForDisplay(currentLine, lineIndex);
            
            // エンドロール風アニメーション開始
            this.animateRoleLine(currentLine, lineIndex);
        }
        
        this.state.currentLine = lineIndex;
    },
    
    // エンドロール用の行準備
    prepareRoleLineForDisplay: function(line, lineIndex) {
        // 基本的な準備
        this.prepareLineForDisplay(line, lineIndex);
        
        // エンドロール固有の設定
        this.applyResponsiveFontSize(line, this.config);
        
        // フェード効果の初期設定
        if (this.roleConfig.fadeEffect) {
            line.style.opacity = '1';
        }
        
        // 初期位置：画面下から開始
        line.style.transform = 'translate(-50%, 100vh)';
        
        console.log(`[ScrollRole] Prepared role line ${lineIndex} for display`);
    },
    
    // エンドロール風アニメーション
    animateRoleLine: function(line, lineIndex) {
        console.log(`[ScrollRole] Starting role animation for line ${lineIndex}`);
        
        // エンドロール風アニメーション開始（下から上へ移動）
        setTimeout(() => {
            line.style.transition = `transform ${this.roleConfig.duration}ms ${this.roleConfig.easing}`;
            line.style.transform = 'translate(-50%, -100vh)';
            
            // フェード効果の追加
            if (this.roleConfig.fadeEffect) {
                this.applyFadeEffect(line);
            }
            
            // 画面を完全に通過した後に非表示
            setTimeout(() => {
                this.cleanupLine(line);
            }, this.roleConfig.duration);
            
        }, this.roleConfig.startDelay);
    },
    
    // フェード効果の適用
    applyFadeEffect: function(line) {
        // 開始時にフェードイン
        line.style.opacity = '0';
        setTimeout(() => {
            line.style.transition += ', opacity 500ms ease-in-out';
            line.style.opacity = '1';
        }, 100);
        
        // 終了時にフェードアウト
        setTimeout(() => {
            line.style.opacity = '0';
        }, this.roleConfig.duration - 1000);
    },
    
    // 行のクリーンアップ
    cleanupLine: function(line) {
        // CSSクラスを削除して非表示に
        line.classList.remove('active');
        line.classList.remove('animating');
        line.style.display = 'none';
        line.style.transition = '';
        line.style.transform = '';
        line.style.opacity = '';
        console.log(`[ScrollRole] Cleaned up line after animation`);
    },
    
    // 行を初期位置にリセット（エンドロール用）
    resetLineToInitialPosition: function(line) {
        line.style.transform = 'translate(-50%, 100vh)';
        
        // roleConfig未初期化時の防御的処理
        if (!this.roleConfig) {
            console.warn('[ScrollRole] roleConfig not initialized, using defaults');
            this.roleConfig = {
                fadeEffect: true,
                continuousDisplay: true,
                scrollDuration: 8000,
                scrollEasing: 'linear',
                lineSpacing: 200,
                duration: 8000,
                easing: 'linear',
                startDelay: 50
            };
        }
        
        line.style.opacity = this.roleConfig.fadeEffect ? '0' : '1';
    },
    
    // 連続表示モードの制御
    setContinuousDisplay: function(enabled) {
        this.roleConfig.continuousDisplay = enabled;
        console.log(`[ScrollRole] Continuous display: ${enabled}`);
    },
    
    // アニメーション速度の調整
    setAnimationSpeed: function(duration) {
        this.roleConfig.duration = duration;
        console.log(`[ScrollRole] Animation duration set to: ${duration}ms`);
    },
    
    // 拡張状態取得
    getState: function() {
        return {
            ...window.ScrollBase.getState.call(this),
            roleConfig: this.roleConfig,
            continuousDisplay: this.roleConfig.continuousDisplay
        };
    }
});