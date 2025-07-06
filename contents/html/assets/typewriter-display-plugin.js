/*
 * ScrollCast Typewriter Display Plugin
 * タイプライター表示プラグイン  
 */

window.TypewriterDisplayPlugin = {
    name: 'typewriter_display',
    
    initialize: function(config) {
        this.config = config;
        this.sentences = document.querySelectorAll('.typewriter-sentence');
        this.setupDisplayHandlers();
        this.initializeDisplay();
    },
    
    setupDisplayHandlers: function() {
        window.addEventListener('sequence_start', (event) => {
            this.playSequence(event.detail.index, event.detail.data);
        });
    },
    
    initializeDisplay: function() {
        this.sentences.forEach(sentence => {
            sentence.style.display = 'none';
            const chars = sentence.querySelectorAll('.typewriter-char');
            chars.forEach(char => {
                char.style.opacity = '0';
                char.style.transform = 'scale(0.8)';
            });
        });
    },
    
    playSequence: function(sequenceIndex, sequenceData) {
        if (sequenceIndex >= this.sentences.length) return;
        
        const sentence = this.sentences[sequenceIndex];
        if (!sentence) return;
        
        this.animateTypewriter(sentence, sequenceData);
    },
    
    animateTypewriter: function(sentence, sequenceData) {
        sentence.style.display = 'block';
        sentence.classList.add('active');
        
        const chars = sentence.querySelectorAll('.typewriter-char');
        const characterTimings = sequenceData.character_timings || [];
        
        characterTimings.forEach((timing, index) => {
            if (index < chars.length) {
                setTimeout(() => {
                    chars[index].style.opacity = '1';
                    chars[index].style.transform = 'scale(1)';
                    chars[index].classList.add('visible');
                }, timing.fade_start_ms || index * 100);
            }
        });
    }
};
