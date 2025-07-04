// ============================================================================
// ScrollCast Core Library - Simple Text Flow Version
// Auto-play only, no interactive features
// ============================================================================

// ============================================================================
// AutoPlayPlugin: Simple Timeline Management
// ============================================================================
window.AutoPlayPlugin = {
    name: 'auto_play',
    
    initialize: function(config) {
        console.log('[AutoPlay] Initializing with config:', config);
        this.config = config;
        this.state = {
            isPlaying: false,
            globalTime: 0,
            startTime: null
        };
        this.timeline = [];
        this.setupTimeline();
        this.setupAutoPlay();
        console.log('[AutoPlay] Initialization complete');
    },
    
    setupTimeline: function() {
        console.log('[AutoPlay] Setting up timeline...');
        // タイミングデータからタイムラインイベントを構築
        if (!this.config.timingData) {
            console.log('[AutoPlay] No timing data found');
            return;
        }
        
        console.log(`[AutoPlay] Found ${this.config.timingData.length} timing entries`);
        
        let cumulativeTime = 0;
        
        this.config.timingData.forEach((sequenceData, index) => {
            // 複数のタイミングデータ形式に対応
            let startTime = sequenceData.start_time || sequenceData.dialogue_start;
            const text = sequenceData.text || sequenceData.dialogue_text || `sequence_${index}`;
            
            // start_timeがない場合は累積タイミングを使用（Railway Scrollなど）
            if (startTime === undefined) {
                startTime = cumulativeTime;
                const duration = sequenceData.total_duration || sequenceData.duration || 4000;
                cumulativeTime += duration;
                console.log(`[AutoPlay] Calculated cumulative timing for sequence ${index}: start=${startTime}ms, duration=${duration}ms`);
            }
            
            this.timeline.push({
                time: startTime,
                type: 'sequence_start',
                index: index,
                data: sequenceData
            });
            
            if (index < 3) {
                console.log(`[AutoPlay] Timeline entry ${index}: start=${startTime}ms, text="${text}"`);
            }
        });
        
        // 総時間を最後の要素の終了時間で計算
        if (this.config.timingData.length > 0) {
            // 累積タイミングを使用した場合はcumulativeTimeを使用
            if (cumulativeTime > 0) {
                this.totalDuration = cumulativeTime;
                console.log(`[AutoPlay] Total duration (cumulative): ${this.totalDuration}ms`);
            } else {
                const lastSequence = this.config.timingData[this.config.timingData.length - 1];
                const lastStartTime = lastSequence.start_time || lastSequence.dialogue_start || 0;
                const lastDuration = lastSequence.duration || lastSequence.dialogue_duration || 8000;
                const lastEndTime = lastSequence.end_time || lastSequence.dialogue_end || (lastStartTime + lastDuration);
                this.totalDuration = Math.max(lastEndTime, lastStartTime + lastDuration);
                console.log(`[AutoPlay] Total duration (explicit): ${this.totalDuration}ms`);
            }
        } else {
            this.totalDuration = 0;
        }
    },
    
    setupAutoPlay: function() {
        console.log('[AutoPlay] Setting up auto-play');
        window.addEventListener('load', () => {
            console.log('[AutoPlay] Window loaded, starting with delay:', this.config.initial_delay || 500);
            setTimeout(() => {
                this.start();
            }, this.config.initial_delay || 500);
        });
    },
    
    start: function() {
        console.log(`[AutoPlay] Starting playback with ${this.timeline.length} timeline events`);
        if (this.timeline.length === 0) {
            console.log('[AutoPlay] No timeline events to play');
            return;
        }
        
        this.state.isPlaying = true;
        this.state.startTime = performance.now();
        console.log('[AutoPlay] Playback started');
        this.tick();
    },
    
    tick: function() {
        if (!this.state.isPlaying) return;
        
        const currentTime = performance.now();
        this.state.globalTime = currentTime - this.state.startTime;
        
        // タイムラインイベントの処理
        this.processTimelineEvents(this.state.globalTime);
        
        // 継続的な時間更新
        if (this.state.globalTime < this.totalDuration) {
            requestAnimationFrame(() => this.tick());
        } else {
            this.state.isPlaying = false;
            this.dispatchEvent('timeline_complete');
        }
    },
    
    processTimelineEvents: function(currentTime) {
        // 未実行のイベントを検索して実行
        this.timeline.forEach(event => {
            if (!event.executed && currentTime >= event.time) {
                console.log(`[AutoPlay] Executing event at ${event.time}ms: sequence ${event.index}`);
                event.executed = true;
                
                if (event.type === 'sequence_start') {
                    this.dispatchEvent('sequence_start', {
                        index: event.index,
                        data: event.data,
                        globalTime: currentTime
                    });
                }
            }
        });
    },
    
    dispatchEvent: function(eventType, detail = {}) {
        console.log(`[AutoPlay] Dispatching event: ${eventType}`, detail);
        window.dispatchEvent(new CustomEvent(eventType, {
            detail: { ...detail, source: 'auto_play' }
        }));
    },
    
    getState: function() {
        return {
            ...this.state,
            progress: this.totalDuration ? this.state.globalTime / this.totalDuration : 0
        };
    }
};

// ============================================================================
// TypewriterDisplayPlugin: Simple Character Animation
// ============================================================================
window.TypewriterDisplayPlugin = {
    name: 'typewriter_display',
    
    initialize: function(config) {
        console.log('[Typewriter] Initializing with config:', config);
        this.config = config;
        this.sentences = document.querySelectorAll('.typewriter-sentence');
        console.log(`[Typewriter] Found ${this.sentences.length} sentences`);
        this.currentSentenceIndex = -1;
        this.setupDisplayHandlers();
        this.initializeDisplay();
        console.log('[Typewriter] Initialization complete');
    },
    
    setupDisplayHandlers: function() {
        console.log('[Typewriter] Setting up event handlers');
        // シンプル自動再生イベントのリスナー
        window.addEventListener('sequence_start', (event) => {
            console.log('[Typewriter] Received sequence_start event:', event.detail);
            this.playSequence(event.detail.index, event.detail.data);
        });
    },
    
    initializeDisplay: function() {
        // 全ての文を非表示に初期化
        this.sentences.forEach((sentence, index) => {
            sentence.classList.remove('active');
            const chars = sentence.querySelectorAll('.typewriter-char');
            chars.forEach(char => {
                char.style.opacity = '0';
            });
        });
    },
    
    playSequence: function(sequenceIndex, sequenceData) {
        console.log(`[Typewriter] playSequence called: index=${sequenceIndex}, total sentences=${this.sentences.length}`);
        
        if (sequenceIndex >= this.sentences.length) {
            console.log(`[Typewriter] Index ${sequenceIndex} out of bounds`);
            return;
        }
        
        // 前の文を非表示
        if (this.currentSentenceIndex >= 0 && this.currentSentenceIndex < this.sentences.length && this.currentSentenceIndex !== sequenceIndex) {
            console.log(`[Typewriter] Hiding previous sentence ${this.currentSentenceIndex}`);
            const prevSentence = this.sentences[this.currentSentenceIndex];
            prevSentence.classList.remove('active');
            
            // 前の文をフェードアウト
            setTimeout(() => {
                prevSentence.style.opacity = '0';
                setTimeout(() => {
                    prevSentence.style.display = 'none';
                }, 300);
            }, 100);
        }
        
        // 新しい文を表示
        this.currentSentenceIndex = sequenceIndex;
        const currentSentence = this.sentences[this.currentSentenceIndex];
        if (currentSentence) {
            console.log(`[Typewriter] Showing sentence ${sequenceIndex}: "${currentSentence.textContent}"`);
            
            // 文を表示状態にする
            currentSentence.style.display = 'block';
            currentSentence.style.opacity = '1';
            currentSentence.classList.add('active');
            
            // タイプライター効果を開始
            this.animateCharactersWithWebAPI(currentSentence, sequenceData, sequenceIndex);
        } else {
            console.log(`[Typewriter] No sentence found at index ${sequenceIndex}`);
        }
    },
    
    animateCharactersWithWebAPI: function(sentence, sequenceData, sequenceIndex) {
        const chars = sentence.querySelectorAll('.typewriter-char');
        console.log(`[Typewriter] Found ${chars.length} characters in sentence ${sequenceIndex}`);
        
        if (chars.length === 0) {
            console.log(`[Typewriter] No characters found for sentence ${sequenceIndex}`);
            return;
        }
        
        // 全文字を初期状態に戻す
        chars.forEach(char => {
            char.style.opacity = '0';
            char.classList.remove('visible');
        });
        
        // 文字データがない場合は基本的なタイプライター効果を作成
        if (!sequenceData.chars) {
            console.log(`[Typewriter] No char timing data, using basic typewriter effect`);
            // 基本的なタイプライター効果（1文字ずつ150ms間隔で表示）
            chars.forEach((char, charIndex) => {
                setTimeout(() => {
                    console.log(`[Typewriter] Showing char ${charIndex}: "${char.textContent}"`);
                    char.style.transition = 'opacity 0.2s ease-in-out';
                    char.style.opacity = '1';
                    char.classList.add('visible');
                }, charIndex * 150);
            });
            return;
        }
        
        console.log(`[Typewriter] Using char timing data with ${sequenceData.chars.length} entries`);
        
        // 各文字のアニメーションを作成
        sequenceData.chars.forEach((charTiming, charIndex) => {
            if (charIndex >= chars.length) return;
            
            const char = chars[charIndex];
            
            // Web Animation API でタイプライター効果
            setTimeout(() => {
                console.log(`[Typewriter] Animating char ${charIndex}: "${char.textContent}" at delay ${charTiming.start || 0}ms`);
                const animation = char.animate([
                    { opacity: 0, offset: 0 },
                    { opacity: 1, offset: 1 }
                ], {
                    duration: charTiming.fade_duration || 200,
                    fill: 'forwards',
                    easing: 'ease-in-out'
                });
                
                animation.addEventListener('finish', () => {
                    char.style.opacity = '1';
                    char.classList.add('visible');
                });
            }, charTiming.start || 0);
        });
    }
};

// ============================================================================
// SimpleRoleDisplayPlugin: Movie Credits Style Animation
// ============================================================================
window.SimpleRoleDisplayPlugin = {
    name: 'simple_role_display',
    
    initialize: function(config) {
        this.config = config;
        this.state = {
            currentLine: 0,
            isDisplaying: false
        };
        this.totalLines = 0;
        this.setupDisplay();
        this.setupEventListeners();
    },
    
    setupDisplay: function() {
        // 行要素を取得
        this.lineElements = document.querySelectorAll('.role-line');
        this.totalLines = this.lineElements.length;
        
        // 初期状態で全ての行を非表示
        this.lineElements.forEach(line => {
            line.style.display = 'none';
        });
        
        // コンテナの設定
        const container = document.querySelector('.role-container');
        if (container) {
            container.style.overflow = 'hidden';
            container.style.height = '100vh';
        }
    },
    
    setupEventListeners: function() {
        // シンプル自動再生イベント
        window.addEventListener('sequence_start', (event) => {
            this.showLine(event.detail.index);
        });
    },
    
    showLine: function(lineIndex) {
        if (lineIndex < 0 || lineIndex >= this.totalLines) return;
        
        console.log(`[SimpleRole] Showing line ${lineIndex}:`, this.lineElements[lineIndex]?.textContent);
        
        // 新しい行を表示
        const currentLine = this.lineElements[lineIndex];
        if (currentLine) {
            currentLine.style.display = 'block';
            currentLine.style.position = 'fixed';
            currentLine.style.left = '50%';
            currentLine.style.top = '0';
            currentLine.style.zIndex = '100';
            currentLine.style.whiteSpace = 'nowrap';
            currentLine.style.fontSize = '3vw';
            currentLine.style.color = '#ffffff';
            currentLine.style.textShadow = '2px 2px 4px rgba(0, 0, 0, 0.8)';
            
            // 初期位置：画面下から開始
            currentLine.style.transform = 'translate(-50%, 100vh)';
            currentLine.style.opacity = '1';
            
            // エンドロール風アニメーション開始（下から上へ8秒で移動）
            setTimeout(() => {
                currentLine.style.transition = 'transform 8s linear';
                currentLine.style.transform = 'translate(-50%, -100vh)';
                
                // 画面を完全に通過した後に非表示
                setTimeout(() => {
                    currentLine.style.display = 'none';
                    currentLine.style.transition = '';
                    currentLine.style.transform = '';
                }, 8000);
            }, 50);
        }
        
        this.state.currentLine = lineIndex;
    },
    
    getState: function() {
        return {
            currentLine: this.state.currentLine,
            totalLines: this.totalLines,
            isDisplaying: this.state.isDisplaying
        };
    }
};

// ============================================================================
// RailwayDisplayPlugin: Railway Sign Style Animation
// ============================================================================
window.RailwayDisplayPlugin = {
    name: 'railway_display',
    
    initialize: function(config) {
        console.log('[Railway] Initializing with config:', config);
        this.config = config;
        this.lines = document.querySelectorAll('.railway-line');
        console.log(`[Railway] Found ${this.lines.length} lines`);
        this.currentLineIndex = 0;
        this.setupDisplayHandlers();
        this.initializeDisplay();
        console.log('[Railway] Initialization complete');
    },
    
    setupDisplayHandlers: function() {
        console.log('[Railway] Setting up event handlers');
        // シンプル自動再生イベントのリスナー
        window.addEventListener('sequence_start', (event) => {
            console.log('[Railway] Received sequence_start event:', event.detail);
            this.playSequence(event.detail.index, event.detail.data);
        });
    },
    
    initializeDisplay: function() {
        // 全ての行を初期状態にリセット
        this.lines.forEach(line => {
            line.className = 'railway-line';
            // 初期位置: 下
            line.style.transform = 'translate(-50%, -50%) translateY(100px)';
            line.style.opacity = '0';
        });
    },
    
    playSequence: function(sequenceIndex, sequenceData) {
        console.log(`[Railway] playSequence called: index=${sequenceIndex}, total lines=${this.lines.length}`);
        
        if (sequenceIndex >= this.lines.length) {
            console.log(`[Railway] Index ${sequenceIndex} out of bounds`);
            return;
        }
        
        // 現在の行を取得
        this.currentLineIndex = sequenceIndex;
        const currentLine = this.lines[this.currentLineIndex];
        if (!currentLine) {
            console.log(`[Railway] No line found at index ${sequenceIndex}`);
            return;
        }
        
        console.log(`[Railway] Animating line ${sequenceIndex}: "${currentLine.textContent}"`);
        
        // Railway scroll 3段階アニメーション (Web Animation API)
        this.animateRailwayLineWithWebAPI(currentLine, sequenceData, sequenceIndex);
    },
    
    animateRailwayLineWithWebAPI: function(line, sequenceData, sequenceIndex) {
        console.log(`[Railway] Starting animation for line ${sequenceIndex}`);
        
        // 前の行を隠す
        if (this.currentAnimatingLine && this.currentAnimatingLine !== line) {
            console.log(`[Railway] Hiding previous line`);
            this.currentAnimatingLine.style.opacity = '0';
            this.currentAnimatingLine.style.transform = 'translate(-50%, -50%) translateY(100px)';
        }
        this.currentAnimatingLine = line;
        
        // 3段階のアニメーションを順次実行
        const phases = this.createRailwayAnimationPhases(line, sequenceData, sequenceIndex);
        console.log(`[Railway] Created ${phases.length} animation phases`);
        
        // Phase 1: フェードイン (下→中央)
        console.log(`[Railway] Starting Phase 1: fade-in`);
        setTimeout(() => {
            const phase1Animation = line.animate(phases[0].keyframes, phases[0].options);
            phase1Animation.addEventListener('finish', () => {
                console.log(`[Railway] Phase 1 completed`);
                if (phases[0].onFinish) phases[0].onFinish(line);
                
                // Phase 2: 静止表示 (中央)
                console.log(`[Railway] Starting Phase 2: static`);
                setTimeout(() => {
                    const phase2Animation = line.animate(phases[1].keyframes, phases[1].options);
                    phase2Animation.addEventListener('finish', () => {
                        console.log(`[Railway] Phase 2 completed`);
                        
                        // Phase 3: フェードアウト (中央→上)
                        console.log(`[Railway] Starting Phase 3: fade-out`);
                        setTimeout(() => {
                            const phase3Animation = line.animate(phases[2].keyframes, phases[2].options);
                            phase3Animation.addEventListener('finish', () => {
                                console.log(`[Railway] Phase 3 completed - line ${sequenceIndex} animation finished`);
                                if (phases[2].onFinish) phases[2].onFinish(line);
                            });
                        }, phases[2].options.delay || 0);
                    });
                }, phases[1].options.delay || 0);
            });
        }, phases[0].options.delay || 0);
    },
    
    createRailwayAnimationPhases: function(line, sequenceData, sequenceIndex) {
        // Parameters kept for future extensibility but not currently used
        // eslint-disable-next-line no-unused-vars
        void line; void sequenceIndex;
        
        const fadeInDuration = sequenceData.fade_in_duration || 800;
        const staticDuration = sequenceData.static_duration || 2000;
        const fadeOutDuration = sequenceData.fade_out_duration || 800;
        
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
                    duration: fadeInDuration,
                    delay: 0,
                    fill: 'forwards',
                    easing: 'ease-in-out'
                },
                onFinish: (line) => {
                    line.style.opacity = '1';
                    line.style.transform = 'translate(-50%, -50%) translateY(0px)';
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
                    duration: staticDuration,
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
                    duration: fadeOutDuration,
                    delay: 0,
                    fill: 'forwards',
                    easing: 'ease-in-out'
                },
                onFinish: (lineElement) => {
                    lineElement.style.opacity = '0';
                    lineElement.style.transform = 'translate(-50%, -50%) translateY(100px)';
                    lineElement.className = 'railway-line';
                }
            }
        ];
    }
};