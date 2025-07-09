// ============================================================================
// Typewriter Base Library - Typewriter系テンプレート共通機能
// ============================================================================

// ScrollCastBaseを継承
window.TypewriterBase = Object.assign({}, window.ScrollCastBase, {
    name: 'typewriter_base',
    
    // Typewriter系共通初期化
    initialize: function(config) {
        console.log('[TypewriterBase] Initializing with config:', config);
        this.initializeCommon(config);
        this.sentences = document.querySelectorAll('.typewriter-sentence');
        console.log(`[TypewriterBase] Found ${this.sentences.length} sentences`);
        this.currentSentenceIndex = -1;
        this.setupTypewriterEventHandlers();
        this.initializeTypewriterDisplay();
        console.log('[TypewriterBase] Initialization complete');
    },
    
    // Typewriter系共通イベントハンドラー
    setupTypewriterEventHandlers: function() {
        console.log('[TypewriterBase] Setting up typewriter event handlers');
        window.addEventListener('sequence_start', (event) => {
            console.log('[TypewriterBase] Received sequence_start event:', event.detail);
            this.playSequence(event.detail.index, event.detail.data);
        });
    },
    
    // Typewriter系共通表示初期化
    initializeTypewriterDisplay: function() {
        // 全ての文を非表示に初期化
        this.sentences.forEach((sentence, index) => {
            sentence.classList.remove('active');
            const chars = sentence.querySelectorAll('.typewriter-char');
            chars.forEach(char => {
                char.style.opacity = '0';
                char.classList.remove('visible');
            });
        });
    },
    
    // 文の切り替え処理（共通）
    playSequence: function(sequenceIndex, sequenceData) {
        console.log(`[TypewriterBase] playSequence called: index=${sequenceIndex}, total sentences=${this.sentences.length}`);
        
        if (sequenceIndex >= this.sentences.length) {
            console.log(`[TypewriterBase] Index ${sequenceIndex} out of bounds`);
            return;
        }
        
        // 前の文を非表示
        this.hidePreviousSentence(sequenceIndex);
        
        // 新しい文を表示
        this.showCurrentSentence(sequenceIndex, sequenceData);
    },
    
    // 前の文を隠す処理
    hidePreviousSentence: function(currentIndex) {
        if (this.currentSentenceIndex >= 0 && 
            this.currentSentenceIndex < this.sentences.length && 
            this.currentSentenceIndex !== currentIndex) {
            
            console.log(`[TypewriterBase] Hiding previous sentence ${this.currentSentenceIndex}`);
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
    },
    
    // 現在の文を表示する処理
    showCurrentSentence: function(sequenceIndex, sequenceData) {
        this.currentSentenceIndex = sequenceIndex;
        const currentSentence = this.sentences[this.currentSentenceIndex];
        
        if (currentSentence) {
            console.log(`[TypewriterBase] Showing sentence ${sequenceIndex}: "${currentSentence.textContent}"`);
            
            // 文を表示状態にする
            currentSentence.style.display = 'block';
            currentSentence.style.opacity = '1';
            currentSentence.classList.add('active');
            
            // 文字アニメーション開始（サブクラスで実装）
            this.animateCharacters(currentSentence, sequenceData, sequenceIndex);
        } else {
            console.log(`[TypewriterBase] No sentence found at index ${sequenceIndex}`);
        }
    },
    
    // 文字アニメーション（サブクラスでオーバーライド）
    animateCharacters: function(sentence, sequenceData, sequenceIndex) {
        console.log('[TypewriterBase] Base character animation - should be overridden by subclass');
        const chars = sentence.querySelectorAll('.typewriter-char');
        
        // デフォルトの基本アニメーション
        chars.forEach((char, index) => {
            setTimeout(() => {
                char.style.opacity = '1';
                char.classList.add('visible');
            }, index * 100);
        });
    },
    
    // 文字要素の取得と初期化（共通ユーティリティ）
    initializeCharacters: function(sentence) {
        const chars = sentence.querySelectorAll('.typewriter-char');
        chars.forEach(char => {
            char.style.opacity = '0';
            char.classList.remove('visible');
        });
        return chars;
    },
    
    // 基本的なタイプライター効果（フォールバック）
    applyBasicTypewriterEffect: function(chars, interval = 150) {
        console.log(`[TypewriterBase] Applying basic typewriter effect with ${interval}ms interval`);
        chars.forEach((char, index) => {
            setTimeout(() => {
                console.log(`[TypewriterBase] Showing char ${index}: "${char.textContent}"`);
                char.style.transition = 'opacity 0.2s ease-in-out';
                char.style.opacity = '1';
                char.classList.add('visible');
            }, index * interval);
        });
    },
    
    // 文字タイミングデータの処理（共通）
    processCharacterTiming: function(chars, sequenceData) {
        // 複数のデータ形式に対応
        const charTimings = sequenceData.character_timings || sequenceData.chars || [];
        
        if (!charTimings || charTimings.length === 0) {
            console.log(`[TypewriterBase] No character timing data, using basic effect`);
            this.applyBasicTypewriterEffect(chars);
            return false;
        }
        
        console.log(`[TypewriterBase] Processing character timing data with ${charTimings.length} entries`);
        return charTimings;
    }
});