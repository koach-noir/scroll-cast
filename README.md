# scroll-cast

Pure text animation generation system for creating engaging, readable content with professional-grade animations.

## Overview

`scroll-cast` is a specialized content generation system that creates HTML-based text animations with precise timing, smooth effects, and mobile-responsive design. It focuses exclusively on text animation generation, following a clean 5-layer architecture for optimal performance and maintainability.

## Architecture

### 5-Layer Architecture
```
Text Input → Boxing → Coloring → Packing → Rendering → HTML Output
```

- **Boxing**: Text processing and formatting for animation
- **Coloring**: Animation timing and effect generation
- **Packing**: ASS subtitle generation
- **Rendering**: HTML/CSS/JS conversion
- **Orchestrator**: Animation workflow coordination

## Features

### Animation Templates
- **Typewriter**: Character-by-character reveal with customizable timing
- **Railway**: Scrolling text with smooth transitions
- **Scroll**: Vertical scrolling with role-based styling

### Output Formats
- **HTML**: Interactive web animations
- **ASS**: Advanced SubStation Alpha subtitle format
- **CSS/JS**: Modular animation components

### Performance
- **209,444 characters/second** processing capability
- **91.5/100** quality scores with comprehensive testing
- **Mobile-responsive** design
- **Type-safe** Pydantic validation

## Installation

```bash
# Clone the repository
git clone https://github.com/koach-noir/scroll-cast.git
cd scroll-cast

# Install dependencies
pip install -r requirements.txt

# Install the package
pip install -e .
```

## Quick Start

```bash
# Generate typewriter animation
scroll-cast generate "Hello World" --template typewriter --output output.html

# Generate railway scroll animation
scroll-cast generate "Your content here" --template railway --output output.html

# Generate with custom config
scroll-cast generate "Custom text" --config config/typewriter_fade.yaml --output output.html
```

## Project Structure

```
scroll-cast/
├── src/
│   └── scrollcast/
│       ├── boxing/          # Text processing
│       ├── coloring/        # Animation effects
│       ├── packing/         # ASS generation
│       ├── rendering/       # HTML conversion
│       └── orchestrator/    # Workflow coordination
├── templates/
│   ├── typewriter/         # Typewriter animation templates
│   ├── railway/            # Railway scroll templates
│   └── scroll/             # Scroll animation templates
├── config/                 # Configuration files
├── docs/                   # Documentation
└── tests/                  # Test suite
```

## CSS Class Standards

scroll-cast follows standardized CSS class naming for integration with decoration systems:

```css
/* Animation elements */
.typewriter-char          /* Individual character */
.typewriter-sentence      /* Sentence container */
.typewriter-container     /* Main container */

.railway-line            /* Railway display line */
.railway-container       /* Railway container */

.scroll-line             /* Scroll text line */
.scroll-container        /* Scroll container */
```

## Integration with Decoration Systems

scroll-cast is designed to work seamlessly with visual decoration systems through CSS override architecture:

```html
<!-- Base animation styles -->
<link rel="stylesheet" href="templates/typewriter/typewriter.css">

<!-- Decoration enhancements (loaded later = higher priority) -->
<link rel="stylesheet" href="decorations/theme.css">
```

## Development

### Running Tests
```bash
# Run all tests
pytest tests/

# Run with coverage
pytest --cov=scrollcast tests/

# Run specific test category
pytest tests/test_animation.py
```

### Code Quality
```bash
# Type checking
mypy src/scrollcast/

# Linting
flake8 src/scrollcast/

# Formatting
black src/scrollcast/
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Ensure all tests pass
6. Submit a pull request

## License

MIT License - see LICENSE file for details.

## Related Projects

- [emotional-decoration](https://github.com/koach-noir/emotional-decoration) - Visual enhancement system for scroll-cast output
- [TextStream](https://github.com/koach-noir/TextStream) - Parent project containing both scroll-cast and emotional-decoration

## Support

For issues, feature requests, or questions, please use the GitHub issue tracker.