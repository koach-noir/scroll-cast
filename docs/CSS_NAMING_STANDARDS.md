# CSS Naming Standards for scroll-cast

## Overview

scroll-cast follows standardized CSS class naming conventions to ensure seamless integration with decoration systems through CSS override architecture. This document defines the naming standards and provides examples for each animation template.

## Core Principles

### 1. Predictable Naming
All CSS classes follow a consistent pattern: `{template}-{element}`

### 2. Hierarchical Structure
Classes are organized in a logical hierarchy from container to individual elements

### 3. Decoration-Friendly
Classes are designed to be easily targeted by decoration systems without conflicts

## Standard Class Names

### Animation Elements

#### Typewriter Template
```css
/* Main container */
.typewriter-container     /* Main animation container */
.typewriter-sentence      /* Sentence container */
.typewriter-char          /* Individual character */
.typewriter-word          /* Word grouping (optional) */
.typewriter-line          /* Line container */

/* States */
.typewriter-char.visible  /* Character is visible */
.typewriter-char.typing   /* Character is being typed */
.typewriter-char.complete /* Character animation complete */
```

#### Railway Template
```css
/* Main container */
.railway-container        /* Main animation container */
.railway-line            /* Individual line */
.railway-char            /* Individual character */
.railway-word            /* Word grouping */
.railway-segment         /* Text segment */

/* States */
.railway-line.active     /* Line is currently scrolling */
.railway-line.complete   /* Line animation complete */
.railway-char.visible    /* Character is visible */
```

#### Scroll Template
```css
/* Main container */
.scroll-container        /* Main animation container */
.scroll-line            /* Individual line */
.scroll-char            /* Individual character */
.scroll-block           /* Text block */
.scroll-role            /* Role indicator */

/* States */
.scroll-line.active     /* Line is currently active */
.scroll-line.complete   /* Line animation complete */
.scroll-char.visible    /* Character is visible */
```

### Decoration Hooks

#### Theme Integration
```css
/* Theme-specific classes */
.theme-learning         /* Learning theme applied */
.theme-emotional        /* Emotional theme applied */
.theme-relaxing         /* Relaxing theme applied */
.theme-professional     /* Professional theme applied */

/* Emotion-specific classes */
.emotion-happy          /* Happy emotion detected */
.emotion-sad            /* Sad emotion detected */
.emotion-excited        /* Excited emotion detected */
.emotion-calm           /* Calm emotion detected */

/* Enhancement markers */
.decoration-enhanced    /* Enhanced by decoration system */
.decoration-gradient    /* Gradient enhancement applied */
.decoration-glow        /* Glow effect applied */
```

## Implementation Guidelines

### 1. Base Animation Styles
scroll-cast provides functional CSS for animations:

```css
/* Example: typewriter.css */
.typewriter-char {
    opacity: 0;
    transition: opacity 0.2s ease-in-out;
    display: inline-block;
    /* No visual styling - only functional properties */
}

.typewriter-sentence {
    display: block;
    text-align: center;
    font-family: Arial, sans-serif;
    /* Basic layout only */
}
```

### 2. Decoration Enhancement
Decoration systems enhance with visual styling:

```css
/* Example: decoration enhancement */
.typewriter-char {
    /* Inherits: opacity, transition, display */
    background: linear-gradient(45deg, var(--theme-start), var(--theme-end));
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    filter: drop-shadow(0 0 2px var(--theme-glow));
}

:root {
    --theme-start: #FF6B6B;
    --theme-end: #4ECDC4;
    --theme-glow: rgba(255, 107, 107, 0.3);
}
```

### 3. CSS Specificity Rules
- Base styles: Low specificity (single class)
- Decoration styles: Higher specificity (can override base)
- User styles: Highest specificity (can override everything)

## Template-Specific Guidelines

### Typewriter Template
- Use `.typewriter-char` for individual character styling
- Use `.typewriter-sentence` for sentence-level effects
- Use `.typewriter-container` for overall layout

### Railway Template
- Use `.railway-line` for scrolling line effects
- Use `.railway-char` for character-level animations
- Use `.railway-container` for viewport and scrolling

### Scroll Template
- Use `.scroll-line` for vertical scrolling effects
- Use `.scroll-role` for role-based styling
- Use `.scroll-container` for overall scrolling behavior

## Integration Examples

### HTML Structure
```html
<!-- scroll-cast generates this structure -->
<div class="typewriter-container">
    <div class="typewriter-sentence">
        <span class="typewriter-char">H</span>
        <span class="typewriter-char">e</span>
        <span class="typewriter-char">l</span>
        <span class="typewriter-char">l</span>
        <span class="typewriter-char">o</span>
    </div>
</div>
```

### CSS Loading Order
```html
<!-- Base animation styles (loaded first) -->
<link rel="stylesheet" href="templates/typewriter/typewriter.css">

<!-- Decoration enhancements (loaded later = higher priority) -->
<link rel="stylesheet" href="decorations/warm-theme.css">

<!-- User customizations (loaded last = highest priority) -->
<link rel="stylesheet" href="custom-styles.css">
```

## Validation Rules

### 1. Naming Validation
- All classes must start with template name
- Use kebab-case for multi-word names
- Avoid abbreviations unless widely understood

### 2. Hierarchy Validation
- Container classes must contain element classes
- State classes must be used with element classes
- Theme classes can be applied to any element

### 3. Decoration Compatibility
- All element classes must be decoration-friendly
- Avoid using `!important` in base styles
- Use CSS custom properties for themeable values

## Testing Standards

### 1. Cross-Template Compatibility
All templates must work with all decoration themes without conflicts.

### 2. CSS Validation
All generated CSS must pass W3C validation.

### 3. Performance Impact
Decoration CSS should not significantly impact animation performance.

## Migration Guide

### From Legacy Naming
If updating from legacy class names:

1. Map old names to new standard names
2. Update all template CSS files
3. Update JavaScript animation logic
4. Test with existing decoration systems

### Version Compatibility
- Major version changes may introduce breaking naming changes
- Minor version changes should maintain backward compatibility
- Patch version changes must not change naming

## Future Considerations

### 1. Semantic Naming
Consider adding semantic class names for better accessibility:
```css
.typewriter-char[data-role="emphasis"]
.typewriter-char[data-emotion="happy"]
```

### 2. CSS-in-JS Integration
Naming standards should work with CSS-in-JS libraries:
```javascript
const styles = {
  typewriterChar: {
    // styles
  }
};
```

### 3. Web Components
Naming should be compatible with Web Components architecture:
```html
<scroll-cast-typewriter>
  <span class="typewriter-char">H</span>
</scroll-cast-typewriter>
```

## Summary

These naming standards ensure that scroll-cast animations integrate seamlessly with decoration systems while maintaining clean, predictable, and maintainable CSS architecture. Following these standards enables the dual repository architecture to work effectively without conflicts or unexpected behavior.