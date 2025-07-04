// ============================================================================
// Railway Base Library - Railway系テンプレート共通機能
// ============================================================================

// ScrollCastBaseを継承
window.RailwayBase = Object.assign({}, window.ScrollCastBase, {
    name: 'railway_base',
    
    // Railway系共通初期化
    initialize: function(config) {
        console.log('[RailwayBase] Initializing with config:', config);
        this.initializeCommon(config);
        this.lines = document.querySelectorAll('.railway-line');
        console.log(`[RailwayBase] Found ${this.lines.length} lines`);
        this.currentLineIndex = 0;
        this.currentAnimatingLine = null;
        this.setupRailwayEventHandlers();
        this.initializeRailwayDisplay();
        console.log('[RailwayBase] Initialization complete');
    },
    
    // Railway系共通イベントハンドラー
    setupRailwayEventHandlers: function() {
        console.log('[RailwayBase] Setting up railway event handlers');
        window.addEventListener('sequence_start', (event) => {
            console.log('[RailwayBase] Received sequence_start event:', event.detail);
            this.playSequence(event.detail.index, event.detail.data);
        });
    },
    
    // Railway系共通表示初期化
    initializeRailwayDisplay: function() {
        // 全ての行を初期状態にリセット
        this.lines.forEach(line => {
            line.className = 'railway-line';
            this.resetLineToInitialPosition(line);
        });
    },
    
    // 行を初期位置にリセット
    resetLineToInitialPosition: function(line) {
        line.style.transform = 'translate(-50%, -50%) translateY(100px) scale(0.9)';
        line.style.opacity = '0';
        line.style.transition = 'none'; // アニメーション競合を防ぐ
    },
    
    // シーケンス再生処理（共通）
    playSequence: function(sequenceIndex, sequenceData) {
        console.log(`[RailwayBase] playSequence called: index=${sequenceIndex}, total lines=${this.lines.length}`);
        
        if (sequenceIndex >= this.lines.length) {
            console.log(`[RailwayBase] Index ${sequenceIndex} out of bounds`);
            return;
        }
        
        // 現在の行を取得
        this.currentLineIndex = sequenceIndex;
        const currentLine = this.lines[this.currentLineIndex];
        if (!currentLine) {
            console.log(`[RailwayBase] No line found at index ${sequenceIndex}`);
            return;
        }
        
        console.log(`[RailwayBase] Animating line ${sequenceIndex}: "${currentLine.textContent}"`);
        
        // 前の行を処理
        this.handlePreviousLine(currentLine);
        
        // 現在の行を表示可能にする
        currentLine.classList.add('active');
        currentLine.classList.add('animating');
        currentLine.style.display = 'block';
        // CSSトランジションを無効化してJSアニメーションを有効にする
        currentLine.style.transition = 'none';
        console.log(`[RailwayBase] Made line ${sequenceIndex} visible with active and animating classes`);
        
        // Railway アニメーション実行（サブクラスで実装）
        this.animateLine(currentLine, sequenceData, sequenceIndex);
    },
    
    // 前の行の処理
    handlePreviousLine: function(currentLine) {
        if (this.currentAnimatingLine && this.currentAnimatingLine !== currentLine) {
            console.log(`[RailwayBase] Hiding previous line`);
            this.currentAnimatingLine.classList.remove('active');
            this.currentAnimatingLine.classList.remove('animating');
            this.currentAnimatingLine.style.display = 'none';
            this.resetLineToInitialPosition(this.currentAnimatingLine);
        }
        this.currentAnimatingLine = currentLine;
    },
    
    // ライン アニメーション（サブクラスでオーバーライド）
    animateLine: function(line, sequenceData, sequenceIndex) {
        console.log('[RailwayBase] Base line animation - should be overridden by subclass');
        // デフォルトの基本アニメーション
        line.style.opacity = '1';
        line.style.transform = 'translate(-50%, -50%) translateY(0px)';
    },
    
    // 3段階アニメーション共通パラメータ取得
    getAnimationPhaseParams: function(sequenceData) {
        return {
            fadeInDuration: sequenceData.fade_in_duration || 800,
            staticDuration: sequenceData.static_duration || 2000,
            fadeOutDuration: sequenceData.fade_out_duration || 800,
            fadeInStart: sequenceData.fade_in_start || 0,
            staticStart: sequenceData.static_start || 800,
            fadeOutStart: sequenceData.fade_out_start || 2800
        };
    },
    
    // 基本的な3段階アニメーションフェーズ作成
    createBasicAnimationPhases: function(sequenceData) {
        const params = this.getAnimationPhaseParams(sequenceData);
        
        return [
            // Phase 1: フェードイン (下→中央)
            {
                name: 'fade-in',
                keyframes: [
                    { 
                        opacity: 0, 
                        transform: 'translate(-50%, -50%) translateY(100px)',
                        offset: 0 
                    },
                    { 
                        opacity: 1, 
                        transform: 'translate(-50%, -50%) translateY(0px)',
                        offset: 1 
                    }
                ],
                options: {
                    duration: params.fadeInDuration,
                    delay: 0,
                    fill: 'forwards',
                    easing: 'ease-in-out'
                },
                onFinish: (lineElement) => {
                    lineElement.style.opacity = '1';
                    lineElement.style.transform = 'translate(-50%, -50%) translateY(0px)';
                }
            },
            
            // Phase 2: 静止表示 (中央)
            {
                name: 'static',
                keyframes: [
                    { 
                        opacity: 1, 
                        transform: 'translate(-50%, -50%) translateY(0px)',
                        offset: 0 
                    },
                    { 
                        opacity: 1, 
                        transform: 'translate(-50%, -50%) translateY(0px)',
                        offset: 1 
                    }
                ],
                options: {
                    duration: params.staticDuration,
                    delay: 0,
                    fill: 'forwards',
                    easing: 'linear'
                }
            },
            
            // Phase 3: フェードアウト (中央→上)
            {
                name: 'fade-out',
                keyframes: [
                    { 
                        opacity: 1, 
                        transform: 'translate(-50%, -50%) translateY(0px)',
                        offset: 0 
                    },
                    { 
                        opacity: 0, 
                        transform: 'translate(-50%, -50%) translateY(-100px)',
                        offset: 1 
                    }
                ],
                options: {
                    duration: params.fadeOutDuration,
                    delay: 0,
                    fill: 'forwards',
                    easing: 'ease-in-out'
                },
                onFinish: (lineElement) => {
                    this.resetLineToInitialPosition(lineElement);
                    lineElement.className = 'railway-line';
                }
            }
        ];
    },
    
    // 順次アニメーション実行ヘルパー
    executeSequentialAnimation: function(line, phases) {
        console.log(`[RailwayBase] Starting sequential animation with ${phases.length} phases`);
        
        // Phase 1: フェードイン
        console.log(`[RailwayBase] Starting Phase 1: fade-in`);
        setTimeout(() => {
            const phase1Animation = line.animate(phases[0].keyframes, phases[0].options);
            phase1Animation.addEventListener('finish', () => {
                console.log(`[RailwayBase] Phase 1 completed`);
                if (phases[0].onFinish) phases[0].onFinish(line);
                
                // Phase 2: 静止表示
                console.log(`[RailwayBase] Starting Phase 2: static`);
                setTimeout(() => {
                    const phase2Animation = line.animate(phases[1].keyframes, phases[1].options);
                    phase2Animation.addEventListener('finish', () => {
                        console.log(`[RailwayBase] Phase 2 completed`);
                        
                        // Phase 3: フェードアウト
                        console.log(`[RailwayBase] Starting Phase 3: fade-out`);
                        setTimeout(() => {
                            const phase3Animation = line.animate(phases[2].keyframes, phases[2].options);
                            phase3Animation.addEventListener('finish', () => {
                                console.log(`[RailwayBase] Phase 3 completed - animation finished`);
                                if (phases[2].onFinish) phases[2].onFinish(line);
                            });
                        }, phases[2].options.delay || 0);
                    });
                }, phases[1].options.delay || 0);
            });
        }, phases[0].options.delay || 0);
    }
});