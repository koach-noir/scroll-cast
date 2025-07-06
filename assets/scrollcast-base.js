// ============================================================================
// ScrollCast Base Library - Core Functionality
// 全テンプレート共通の基本機能
// ============================================================================

// ============================================================================
// AutoPlayPlugin: Timeline Management
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
        
        // 総時間を正しく計算
        if (this.config.timingData.length > 0) {
            const lastSequence = this.config.timingData[this.config.timingData.length - 1];
            
            // 明示的な終了時間があればそれを使用
            if (lastSequence.end_time) {
                this.totalDuration = lastSequence.end_time;
                console.log(`[AutoPlay] Total duration (end_time): ${this.totalDuration}ms`);
            } else {
                // start_time + duration で計算
                const lastStartTime = lastSequence.start_time || 0;
                const lastDuration = lastSequence.duration || 4000;
                this.totalDuration = lastStartTime + lastDuration;
                console.log(`[AutoPlay] Total duration (start+duration): ${this.totalDuration}ms`);
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
// ScrollCastBase: 共通基盤機能
// ============================================================================
window.ScrollCastBase = {
    // 共通初期化処理
    initializeCommon: function(config) {
        this.config = config;
        this.setupCommonEventHandlers();
        console.log('[ScrollCastBase] Common initialization complete');
    },
    
    // 共通イベントハンドラー設定
    setupCommonEventHandlers: function() {
        // 共通のキーボードイベントなど
        document.addEventListener('keydown', (event) => {
            if (event.code === 'Space') {
                event.preventDefault();
                this.togglePlayback && this.togglePlayback();
            }
        });
    },
    
    // 共通ユーティリティ関数
    utils: {
        // 要素の初期化
        resetElement: function(element) {
            element.style.opacity = '0';
            element.style.transform = '';
            element.style.transition = '';
        },
        
        // CSS変数の設定
        setCSSVariable: function(name, value) {
            document.documentElement.style.setProperty(name, value);
        },
        
        // デバイス判定
        isMobile: function() {
            return window.innerWidth <= 768;
        }
    }
};