// ============================================================================
// Railway Scroll Plugin - 鉄道方向幕風スクロール効果
// ============================================================================

// RailwayBaseを継承
window.RailwayScrollPlugin = Object.assign({}, window.RailwayBase, {
    name: 'railway_scroll',
    
    // スクロール効果固有の初期化
    initialize: function(config) {
        console.log('[RailwayScroll] Initializing scroll-specific features');
        // 基底クラスの初期化を呼び出し
        window.RailwayBase.initialize.call(this, config);
        
        // スクロール効果固有の設定
        this.scrollConfig = {
            animationDuration: config.animation_duration || 800,
            scrollEasing: config.scroll_easing || 'ease-in-out',
            verticalOffset: config.vertical_offset || 100
        };
        
        console.log('[RailwayScroll] Config values received:', {
            animation_duration: config.animation_duration,
            vertical_offset: config.vertical_offset,
            scroll_easing: config.scroll_easing
        });
        
        console.log('[RailwayScroll] Scroll configuration:', this.scrollConfig);
    },
    
    // ラインアニメーション（スクロール効果）をオーバーライド
    animateLine: function(line, sequenceData, sequenceIndex) {
        console.log(`[RailwayScroll] Starting scroll animation for line ${sequenceIndex}`);
        
        // 3段階のスクロールアニメーションフェーズを作成
        const phases = this.createScrollAnimationPhases(sequenceData);
        console.log(`[RailwayScroll] Created ${phases.length} animation phases`);
        
        // 順次アニメーション実行
        this.executeSequentialAnimation(line, phases);
    },
    
    // スクロール効果専用のアニメーションフェーズ作成
    createScrollAnimationPhases: function(sequenceData) {
        // 基本フェーズを取得
        const basePhases = this.createBasicAnimationPhases(sequenceData);
        
        // スクロール効果の調整
        if (!this.scrollConfig) {
            console.error('[RailwayScroll] scrollConfig is undefined, using defaults');
            this.scrollConfig = {
                animationDuration: 800,
                scrollEasing: 'ease-in-out',
                verticalOffset: 100
            };
        }
        const verticalOffset = this.scrollConfig.verticalOffset;
        
        // Phase 1をスクロール効果用に調整
        basePhases[0].keyframes = [
            { 
                opacity: 0, 
                transform: `translate(-50%, -50%) translateY(${verticalOffset}px) scale(0.9)`,
                offset: 0 
            },
            { 
                opacity: 1, 
                transform: 'translate(-50%, -50%) translateY(0px) scale(1)',
                offset: 1 
            }
        ];
        basePhases[0].options.easing = this.scrollConfig.scrollEasing;
        
        // Phase 3をスクロール効果用に調整
        basePhases[2].keyframes = [
            { 
                opacity: 1, 
                transform: 'translate(-50%, -50%) translateY(0px) scale(1)',
                offset: 0 
            },
            { 
                opacity: 0, 
                transform: `translate(-50%, -50%) translateY(-${verticalOffset}px) scale(0.9)`,
                offset: 1 
            }
        ];
        basePhases[2].options.easing = this.scrollConfig.scrollEasing;
        
        // onFinishコールバックを更新
        basePhases[0].onFinish = (lineElement) => {
            lineElement.style.opacity = '1';
            lineElement.style.transform = 'translate(-50%, -50%) translateY(0px) scale(1)';
        };
        
        basePhases[2].onFinish = (lineElement) => {
            this.resetLineToInitialPosition(lineElement);
            lineElement.classList.remove('active');
            lineElement.classList.remove('animating');
            lineElement.style.display = 'none';
            lineElement.className = 'text-line';
            console.log(`[RailwayScroll] Line animation completed and reset`);
        };
        
        return basePhases;
    },
    
    // 行を初期位置にリセット（スクロール効果用）
    resetLineToInitialPosition: function(line) {
        if (!this.scrollConfig) {
            this.scrollConfig = {
                animationDuration: 800,
                scrollEasing: 'ease-in-out',
                verticalOffset: 100
            };
        }
        const verticalOffset = this.scrollConfig.verticalOffset;
        line.style.transform = `translate(-50%, -50%) translateY(${verticalOffset}px) scale(0.9)`;
        line.style.opacity = '0';
    },
    
    // 強化されたスクロール効果
    enhanceScrollEffect: function(line) {
        // ブラー効果の追加（オプション）
        line.style.filter = 'blur(1px)';
        line.style.transition = 'filter 0.3s ease-in-out';
        
        setTimeout(() => {
            line.style.filter = 'blur(0px)';
        }, 200);
    },
    
    // 前の行の処理（スクロール効果強化版）
    handlePreviousLine: function(currentLine) {
        if (this.currentAnimatingLine && this.currentAnimatingLine !== currentLine) {
            console.log(`[RailwayScroll] Hiding previous line with scroll effect`);
            
            // 前の行にフェードアウト効果を適用
            const prevLine = this.currentAnimatingLine;
            prevLine.style.transition = 'opacity 0.3s ease-out, transform 0.3s ease-out';
            prevLine.style.opacity = '0';
            prevLine.style.transform = 'translate(-50%, -50%) translateY(-50px) scale(0.95)';
            
            setTimeout(() => {
                this.resetLineToInitialPosition(prevLine);
            }, 300);
        }
        this.currentAnimatingLine = currentLine;
    }
});