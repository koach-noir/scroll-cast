/*
 * Revolver Up Template JavaScript - 2024 Modern Implementation
 * CSS Scroll-Driven Animationsがメイン、JavaScriptはフォールバック用
 */

// CSS Scroll-Driven Animations対応確認
const supportsScrollDrivenAnimations = CSS.supports('animation-timeline', 'view()');

console.log('[RevolverUp] Template JavaScript loaded');
console.log(`[RevolverUp] CSS Scroll-Driven Animations support: ${supportsScrollDrivenAnimations}`);

if (!supportsScrollDrivenAnimations) {
    console.log('[RevolverUp] Using JavaScript fallback for scroll animations');
    
    // フォールバック用: Intersection Observer でハイライト効果
    document.addEventListener('DOMContentLoaded', function() {
        const textLines = document.querySelectorAll('.text-line');
        
        if (textLines.length === 0) return;
        
        const observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    // ビューポート中央付近でハイライト
                    const rect = entry.boundingClientRect;
                    const viewportCenter = window.innerHeight / 2;
                    const elementCenter = rect.top + (rect.height / 2);
                    const distance = Math.abs(elementCenter - viewportCenter);
                    const threshold = window.innerHeight * 0.2; // 20%の範囲
                    
                    if (distance < threshold) {
                        entry.target.classList.add('js-highlight');
                    } else {
                        entry.target.classList.remove('js-highlight');
                    }
                } else {
                    entry.target.classList.remove('js-highlight');
                }
            });
        }, {
            threshold: [0, 0.25, 0.5, 0.75, 1.0],
            rootMargin: '-20% 0px -20% 0px'
        });
        
        textLines.forEach(line => observer.observe(line));
    });
} else {
    console.log('[RevolverUp] Using native CSS Scroll-Driven Animations - no JavaScript needed');
}