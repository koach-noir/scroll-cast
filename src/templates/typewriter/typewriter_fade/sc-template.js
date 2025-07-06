// ============================================================================
// Typewriter Fade Plugin - フェード効果付きタイプライター
// ============================================================================

// TypewriterBaseを継承
window.TypewriterFadePlugin = Object.assign({}, window.TypewriterBase, {
    name: 'typewriter_fade',
    
    // フェード効果固有の初期化
    initialize: function(config) {
        console.log('[TypewriterFade] Initializing fade-specific features');
        // 基底クラスの初期化を呼び出し
        window.TypewriterBase.initialize.call(this, config);
        
        // フェード効果固有の設定
        this.fadeConfig = {
            characterFadeDuration: config.character_fade_duration || 200,
            sentenceFadeDuration: config.sentence_fade_duration || 300,
            fadeEasing: config.fade_easing || 'ease-in-out'
        };
        
        console.log('[TypewriterFade] Fade configuration:', this.fadeConfig);
    },
    
    // 文字アニメーション（フェード効果）をオーバーライド
    animateCharacters: function(sentence, sequenceData, sequenceIndex) {
        const chars = this.initializeCharacters(sentence);
        console.log(`[TypewriterFade] Found ${chars.length} characters in sentence ${sequenceIndex}`);
        
        if (chars.length === 0) {
            console.log(`[TypewriterFade] No characters found for sentence ${sequenceIndex}`);
            return;
        }
        
        // 文字タイミングデータの処理
        const charTimings = this.processCharacterTiming(chars, sequenceData);
        if (!charTimings) {
            // タイミングデータがない場合は基本効果を適用
            return;
        }
        
        console.log(`[TypewriterFade] Using character timing data with ${charTimings.length} entries`);
        
        // フェード効果付き文字アニメーション
        this.animateCharactersWithFade(chars, charTimings);
    },
    
    // フェード効果付き文字アニメーション
    animateCharactersWithFade: function(chars, charTimings) {
        charTimings.forEach((charTiming, charIndex) => {
            if (charIndex >= chars.length) return;
            
            const char = chars[charIndex];
            
            // フェード効果のWeb Animation API
            const delay = charTiming.fade_start_ms || charTiming.start || 0;
            setTimeout(() => {
                console.log(`[TypewriterFade] Animating char ${charIndex}: "${char.textContent}" with fade at delay ${delay}ms`);
                
                // フェードイン アニメーション
                const fadeDuration = (charTiming.fade_end_ms - charTiming.fade_start_ms) || charTiming.fade_duration || this.fadeConfig.characterFadeDuration;
                const animation = char.animate([
                    { 
                        opacity: 0, 
                        transform: 'scale(0.8)',
                        offset: 0 
                    },
                    { 
                        opacity: 1, 
                        transform: 'scale(1)',
                        offset: 1 
                    }
                ], {
                    duration: fadeDuration,
                    fill: 'forwards',
                    easing: this.fadeConfig.fadeEasing
                });
                
                animation.addEventListener('finish', () => {
                    char.style.opacity = '1';
                    char.style.transform = 'scale(1)';
                    char.classList.add('visible');
                });
            }, delay);
        });
    },
    
    // 基本タイプライター効果をフェード付きでオーバーライド
    applyBasicTypewriterEffect: function(chars, interval = 150) {
        console.log(`[TypewriterFade] Applying fade-enhanced typewriter effect with ${interval}ms interval`);
        chars.forEach((char, index) => {
            setTimeout(() => {
                console.log(`[TypewriterFade] Showing char ${index} with fade: "${char.textContent}"`);
                
                // フェード効果付きの基本アニメーション
                char.style.transition = `opacity ${this.fadeConfig.characterFadeDuration}ms ${this.fadeConfig.fadeEasing}, transform ${this.fadeConfig.characterFadeDuration}ms ${this.fadeConfig.fadeEasing}`;
                char.style.transform = 'scale(0.8)';
                char.style.opacity = '0';
                
                // 少し遅らせてフェードイン
                setTimeout(() => {
                    char.style.opacity = '1';
                    char.style.transform = 'scale(1)';
                    char.classList.add('visible');
                }, 10);
                
            }, index * interval);
        });
    },
    
    // 文の切り替え時のフェード効果を強化
    hidePreviousSentence: function(currentIndex) {
        if (this.currentSentenceIndex >= 0 && 
            this.currentSentenceIndex < this.sentences.length && 
            this.currentSentenceIndex !== currentIndex) {
            
            console.log(`[TypewriterFade] Hiding previous sentence ${this.currentSentenceIndex} with fade`);
            const prevSentence = this.sentences[this.currentSentenceIndex];
            prevSentence.classList.remove('active');
            
            // 強化されたフェードアウト
            prevSentence.style.transition = `opacity ${this.fadeConfig.sentenceFadeDuration}ms ${this.fadeConfig.fadeEasing}`;
            setTimeout(() => {
                prevSentence.style.opacity = '0';
                setTimeout(() => {
                    prevSentence.style.display = 'none';
                }, this.fadeConfig.sentenceFadeDuration);
            }, 100);
        }
    },
    
    // 文の表示時のフェード効果を強化
    showCurrentSentence: function(sequenceIndex, sequenceData) {
        this.currentSentenceIndex = sequenceIndex;
        const currentSentence = this.sentences[this.currentSentenceIndex];
        
        if (currentSentence) {
            console.log(`[TypewriterFade] Showing sentence ${sequenceIndex} with fade: "${currentSentence.textContent}"`);
            
            // フェードイン効果で文を表示
            currentSentence.style.display = 'block';
            currentSentence.style.opacity = '0';
            currentSentence.style.transition = `opacity ${this.fadeConfig.sentenceFadeDuration}ms ${this.fadeConfig.fadeEasing}`;
            currentSentence.classList.add('active');
            
            // 少し遅らせてフェードイン
            setTimeout(() => {
                currentSentence.style.opacity = '1';
                // 文字アニメーション開始
                this.animateCharacters(currentSentence, sequenceData, sequenceIndex);
            }, 50);
            
        } else {
            console.log(`[TypewriterFade] No sentence found at index ${sequenceIndex}`);
        }
    }
});