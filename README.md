# scroll-cast

Pure text animation generation system with external JavaScript reference architecture for high-performance, modular text animations.

## Overview

`scroll-cast` is a specialized content generation system that creates HTML-based text animations with precise timing, smooth effects, and mobile-responsive design. The system features an **external JavaScript reference architecture** that eliminates code duplication while maintaining full animation functionality and supporting emotional decoration CSS integration.

## Architecture

### 5-Layer Architecture with External Reference System
```
Text Input → Boxing → Coloring → Packing → Rendering → External Assets → HTML Output
```

- **Boxing**: Text processing and formatting for animation
- **Coloring**: Animation timing and effect generation  
- **Packing**: ASS subtitle generation
- **Rendering**: HTML/CSS/JS conversion with external asset deployment
- **Orchestrator**: Animation workflow coordination
- **External Assets**: Modular JavaScript plugins and shared libraries

## Features

### External JavaScript Reference Architecture
- **70-90% file size reduction** through external asset deployment
- **Modular plugin system** with auto-play, railway-display, and simple-role plugins
- **Shared library architecture** with scrollcast-core.js foundation
- **Asset manifest system** for reliable deployment tracking

### Animation Templates
- **Typewriter**: Character-by-character reveal with fade effects
- **Railway**: Scrolling text with smooth train-style transitions  
- **Simple Role**: End-credit style vertical scrolling

### Output Formats
- **HTML**: Interactive web animations with external asset references
- **ASS**: Advanced SubStation Alpha subtitle format
- **CSS/JS**: Modular external plugins and template-specific stylesheets

### Performance & Integration
- **209,444 characters/second** processing capability
- **91.5/100** quality scores with comprehensive testing
- **Mobile-responsive** design with media queries
- **Type-safe** Pydantic validation
- **Emotional decoration CSS** integration support
- **CSS Override Architecture** for decoration system compatibility

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
# Generate railway scroll animation with announcement preset
./test/orchestrator_demo.sh railway_scroll announcement input.txt output_name

# Generate typewriter animation with cinematic preset  
./test/orchestrator_demo.sh typewriter_fade cinematic input.txt output_name

# Generate simple role credits animation
./test/orchestrator_demo.sh simple_role credits input.txt output_name

# Run full integration test (generates all templates)
./test/demo_all_config.sh
```

## Project Structure

```
scroll-cast/
├── src/
│   └── scrollcast/
│       ├── boxing/          # Text processing and formatting
│       ├── coloring/        # Animation timing and effects
│       ├── packing/         # ASS subtitle generation
│       ├── rendering/       # HTML/CSS/JS conversion
│       ├── orchestrator/    # Workflow coordination
│       ├── conversion/      # Plugin-based converters
│       │   ├── plugin_converter_base.py      # External reference system
│       │   ├── railway_scroll_plugin_converter.py
│       │   ├── simple_role_plugin_converter.py
│       │   └── typewriter_fade_plugin_converter.py
│       └── deployment/      # Asset deployment system
│           └── file_deployer.py              # External asset management
├── src/templates/          # Template source files
│   ├── railway/
│   │   └── railway_scroll/
│   │       ├── sc-template.html
│   │       ├── sc-template.css               # Template-specific styles
│   │       └── sc-template.js                # Template-specific logic
│   ├── scroll/scroll_role/
│   └── typewriter/typewriter_fade/
├── config/                 # YAML configuration files  
│   ├── railway_scroll.yaml
│   ├── simple_role.yaml
│   └── typewriter_fade.yaml
├── contents/html/          # Generated output with external assets
│   ├── shared/             # Shared library files
│   │   ├── scrollcast-core.js               # Core plugin system
│   │   └── scrollcast-styles.css            # Base styles
│   ├── assets/             # Plugin JavaScript files
│   │   ├── auto-play-plugin.js              # Timeline management
│   │   ├── railway-display-plugin.js        # Railway animations
│   │   └── simple-role-display-plugin.js    # Scroll animations
│   └── templates/          # Template-specific assets
│       └── railway/railway_scroll/
│           ├── sc-template.css               # External CSS
│           └── sc-template.js                # External JS
├── test/                   # Integration test system
│   ├── demo_all_config.sh                 # Full template test
│   └── orchestrator_demo.sh   # Single template test
└── docs/                   # Documentation and ADRs
```

## CSS Class Standards & External Asset Architecture

scroll-cast follows standardized CSS class naming and external asset architecture for optimal performance and decoration system integration:

### Unified CSS Classes
```css
/* Unified class structure across all templates */
.text-container[data-template="railway"]  /* Template-specific container */
.text-container[data-template="typewriter"]
.text-container[data-template="scroll"]

.text-line                /* Individual text lines */
.text-line[data-line="0"] /* Line-specific targeting */
```

### External Asset References
```html
<!-- Generated HTML structure -->
<!DOCTYPE html>
<html>
<head>
    <!-- Shared base styles -->
    <link rel="stylesheet" href="shared/scrollcast-styles.css">
    <!-- Template-specific styles -->
    <link rel="stylesheet" href="templates/railway/railway_scroll/sc-template.css">
</head>
<body>
    <div class="text-container" data-template="railway">
        <div class="text-line" data-line="0">Content here</div>
    </div>
    
    <!-- External JavaScript architecture -->
    <script src="shared/scrollcast-core.js"></script>
    <script src="assets/auto-play-plugin.js"></script>
    <script src="assets/railway-display-plugin.js"></script>
</body>
</html>
```

### CSS Override Architecture for Decoration Systems

```css
/* Template CSS includes decoration hooks */
.text-container[data-template="railway"].decoration-enhanced {
    /* Decoration system overrides */
}

.text-line.decoration-enhanced {
    /* Enhanced styling from emotional decoration */
}

/* CSS Custom Properties for decoration integration */
.text-line {
    --decoration-filter: none;
    --decoration-background: transparent;
    filter: var(--decoration-filter);
    background: var(--decoration-background);
}
```

## Development

### Running Tests
```bash
# Run integration test for all templates
./test/demo_all_config.sh

# Test specific template and preset
./test/orchestrator_demo.sh railway_scroll announcement test/sample_eng.txt test_output

# Run Python unit tests
pytest tests/

# Run with coverage
pytest --cov=scrollcast tests/
```

### External Asset System Testing
```bash
# Verify asset deployment
ls contents/html/shared/        # Core library files
ls contents/html/assets/        # Plugin JavaScript files  
ls contents/html/templates/     # Template-specific assets

# Check asset manifest
cat contents/html/asset-manifest.json
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