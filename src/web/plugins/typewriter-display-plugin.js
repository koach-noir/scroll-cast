/*
 * ScrollCast Typewriter Display Plugin
 * タイプライター表示プラグイン  
 */

window.TypewriterDisplayPlugin = {
    name: 'typewriter_display',
    
    initialize: function(config) {
        console.log('[DEBUG] TypewriterDisplayPlugin.initialize() called with config:', config);
        this.config = config;
        this.sentences = document.querySelectorAll('.text-container[data-template="typewriter"] .text-sentence, .text-container[data-template="typewriter"] .typewriter-sentence, .typewriter-sentence');
        console.log('[DEBUG] Found', this.sentences.length, 'sentence elements');
        this.setupDisplayHandlers();
        this.initializeDisplay();
        console.log('[DEBUG] TypewriterDisplayPlugin initialization complete');
    },
    
    setupDisplayHandlers: function() {
        console.log('[DEBUG] setupDisplayHandlers() called');
        window.addEventListener('sequence_start', (event) => {
            console.log('[DEBUG] sequence_start event received:', event.detail);
            this.playSequence(event.detail.index, event.detail.data);
        });
        console.log('[DEBUG] Event listeners set up');
    },
    
    initializeDisplay: function() {
        this.sentences.forEach(sentence => {
            sentence.style.display = 'none';
            const chars = sentence.querySelectorAll('.text-char, .typewriter-char');
            chars.forEach(char => {
                char.style.opacity = '0';
                char.style.transform = 'scale(0.8)';
            });
        });
    },
    
    playSequence: function(sequenceIndex, sequenceData) {
        console.log('[DEBUG] playSequence() called with index:', sequenceIndex);
        if (sequenceIndex >= this.sentences.length) {
            console.log('[DEBUG] Invalid sequence index:', sequenceIndex, 'total sentences:', this.sentences.length);
            return;
        }
        
        const sentence = this.sentences[sequenceIndex];
        if (!sentence) {
            console.log('[DEBUG] No sentence element found at index:', sequenceIndex);
            return;
        }
        
        console.log('[DEBUG] Animating sentence:', sentence.textContent);
        this.animateTypewriter(sentence, sequenceData);
    },
    
    animateTypewriter: function(sentence, sequenceData) {
        console.log('[DEBUG] Starting typewriter animation for sentence:', sentence.textContent);
        console.log('[DEBUG] Full sequenceData:', sequenceData);
        
        // Clear all previous sentences before starting new one
        this.clearPreviousSentences(sentence);
        
        sentence.style.display = 'block';
        sentence.classList.add('active');
        
        const chars = sentence.querySelectorAll('.typewriter-char');
        const characterTimings = sequenceData.character_timings || sequenceData.chars || [];
        
        console.log('[DEBUG] Found', chars.length, 'characters, timings length:', characterTimings.length);
        console.log('[DEBUG] Character timings:', characterTimings);
        
        characterTimings.forEach((timing, index) => {
            if (index < chars.length) {
                const delay = timing.start || timing.fade_start_ms || index * 100;
                console.log('[DEBUG] Setting timeout for char', index, 'at', delay, 'ms');
                setTimeout(() => {
                    chars[index].style.opacity = '1';
                    chars[index].style.transform = 'scale(1)';
                    chars[index].classList.add('visible');
                    console.log('[DEBUG] Character', index, 'displayed:', chars[index].textContent);
                }, delay);
            }
        });
    },
    
    clearPreviousSentences: function(currentSentence) {
        console.log('[DEBUG] Clearing previous sentences');
        this.sentences.forEach(sentence => {
            if (sentence !== currentSentence) {
                sentence.style.display = 'none';
                sentence.classList.remove('active');
                const chars = sentence.querySelectorAll('.text-char, .typewriter-char');
                chars.forEach(char => {
                    char.style.opacity = '0';
                    char.style.transform = 'scale(0.8)';
                    char.classList.remove('visible');
                });
            }
        });
    }
};