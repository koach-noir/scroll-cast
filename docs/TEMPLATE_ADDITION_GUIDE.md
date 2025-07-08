# Template Addition Guide for scroll-cast

## ⚠️ CRITICAL WARNING ⚠️

**BEFORE YOU START**: Adding a new template INCORRECTLY will break ALL existing templates and corrupt the entire system. Follow this guide EXACTLY or you will need to completely rollback your changes.

**ABSOLUTE RULE**: If `git status --porcelain` shows ANY existing files modified (not just new files added), you have violated the isolation principle and MUST immediately rollback all changes.

## Overview

This guide provides a step-by-step process for adding new animation templates to the scroll-cast system, based on lessons learned from multiple implementation failures including horizontal_ticker and vertical_drop that corrupted existing templates.

## Prerequisites

Before adding a new template, you must understand:

1. **5-Layer Architecture**: Boxing → Coloring → Packing → Rendering → Orchestrator
2. **External JavaScript Reference Architecture**: Shared libraries and modular plugins
3. **CSS Override Architecture**: For decoration system compatibility
4. **Plugin-Based Converter System**: All templates use PluginConverterBase
5. **Integration Testing Workflow**: Must work with `integration_test.sh`

## Step-by-Step Implementation Process

### Phase 1: Architecture Planning

#### 1.1 Study Existing Templates
```bash
# Study the three working templates
ls src/templates/
├── railway/railway_scroll/
├── scroll/scroll_role/
└── typewriter/typewriter_fade/

# Examine their converters
ls src/scrollcast/conversion/
├── railway_scroll_plugin_converter.py
├── simple_role_plugin_converter.py
└── typewriter_fade_plugin_converter.py
```

#### 1.2 Define Template Requirements
- **Animation Type**: What kind of animation? (scrolling, typing, fading, etc.)
- **Text Processing**: How should text be broken down? (characters, words, lines)
- **Timing Model**: How should animation timing be calculated?
- **CSS Classes**: What classes follow the naming standards?

### Phase 2: File Structure Creation

#### 2.1 Create Template Directory Structure
```bash
mkdir -p src/templates/{category}/{template_name}/
```

#### 2.2 Create Required Template Files
```bash
# Create the three required template files
touch src/templates/{category}/{template_name}/sc-template.html
touch src/templates/{category}/{template_name}/sc-template.css  
touch src/templates/{category}/{template_name}/sc-template.js
```

**CRITICAL**: Follow the exact naming convention: `sc-template.{html,css,js}`

### Phase 3: HTML Template Implementation

#### 3.1 HTML Structure Requirements
```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{TITLE}}</title>
    <!-- External CSS includes -->
    <link rel="stylesheet" href="shared/scrollcast-styles.css">
    <link rel="stylesheet" href="templates/{category}/{template_name}/sc-template.css">
</head>
<body>
    <!-- UNIFIED CLASS STRUCTURE -->
    <div class="text-container" data-template="{template_name}">
        {{CONTENT_HTML}}
    </div>
    
    <!-- External JavaScript architecture -->
    <script src="shared/scrollcast-core.js"></script>
    <script src="assets/auto-play-plugin.js"></script>
    <script src="assets/{template_name}-display-plugin.js"></script>
    
    <!-- Timing data for auto-play -->
    <script>
        window.timingData = {{TIMING_DATA_JSON}};
    </script>
</body>
</html>
```

**CRITICAL REQUIREMENTS**:
- Use `{{TITLE}}`, `{{CONTENT_HTML}}`, `{{TIMING_DATA_JSON}}` placeholders
- Follow unified CSS class structure: `.text-container[data-template="name"]`
- Include external asset references (shared libraries + template-specific)
- Use the exact external JavaScript reference architecture

#### 3.2 CSS Naming Standards Compliance
```css
/* Template-specific container */
.text-container[data-template="{template_name}"] {
    /* Container styles */
}

/* Standard text line class */
.text-line {
    /* Base line styles */
}

/* Template-specific line styling */
.text-container[data-template="{template_name}"] .text-line {
    /* Template-specific line styles */
}

/* Animation-specific classes */
.{template_name}-element {
    /* Follow naming: {template}-{element} */
}

/* Decoration hooks */
.text-line.decoration-enhanced {
    /* CSS Override Architecture support */
}
```

### Phase 4: Plugin Converter Implementation

#### 4.1 Create Converter Class
```python
# src/scrollcast/conversion/{template_name}_plugin_converter.py
from typing import List
import json
from .plugin_converter_base import PluginConverterBase
from ..coloring.timing_models import TextTiming

class {TemplateName}PluginConverter(PluginConverterBase):
    """
    Converter for {template_name} animation template.
    
    Follows external JavaScript reference architecture with:
    - Template-based HTML generation
    - External asset deployment
    - Unified CSS class structure
    """
    
    def __init__(self, ass_content: str, config: dict):
        super().__init__(ass_content, config)
        self.timings: List[TextTiming] = []
        self._parse_ass_content()
    
    def _parse_ass_content(self) -> None:
        """Parse ASS content and extract timing data."""
        # Implementation specific to your template's needs
        pass
    
    def _get_template_name(self) -> str:
        """Return the template directory name."""
        return "{template_name}"
    
    def _get_template_category(self) -> str:
        """Return the template category."""
        return "{category}"
    
    def _build_content_html(self) -> str:
        """Generate content HTML with unified CSS classes."""
        content_parts = []
        for i, timing in enumerate(self.timings):
            content_parts.append(
                f'<div class="text-line" data-line="{i}">'
                f'{timing.text}</div>'
            )
        return '\n'.join(content_parts)
    
    def _get_timing_data_json(self) -> str:
        """Generate timing data for auto-play plugin."""
        timing_entries = []
        for timing in self.timings:
            timing_entries.append({
                "text": timing.text,
                "start_time": timing.start_time_ms,
                "duration": timing.duration_ms,
                "line_index": timing.line_index
            })
        return json.dumps(timing_entries, ensure_ascii=False, indent=2)
    
    def _get_title(self) -> str:
        """Generate page title."""
        return f"{self.config.get('title', 'ScrollCast Animation')}"
```

**CRITICAL REQUIREMENTS**:
- Inherit from `PluginConverterBase`
- Implement ALL abstract methods
- Use unified CSS class structure
- Generate proper timing data JSON
- Follow external asset architecture

#### 4.2 Required Abstract Methods
```python
# You MUST implement these methods from PluginConverterBase:
def _get_template_name(self) -> str:
    """Template directory name"""
    
def _get_template_category(self) -> str:
    """Template category directory"""
    
def _build_content_html(self) -> str:
    """Generate content HTML with proper CSS classes"""
    
def _get_timing_data_json(self) -> str:
    """Generate timing data for auto-play plugin"""
    
def _get_title(self) -> str:
    """Generate page title"""
```

### Phase 5: External Asset Implementation

#### 5.1 Update file_deployer.py
```python
# src/scrollcast/deployment/file_deployer.py
# Add your template's display plugin

def _get_{template_name}_display_plugin_js(self) -> str:
    return """
    window.{TemplateName}DisplayPlugin = {
        name: '{template_name}_display',
        
        initialize: function(config) {
            this.container = document.querySelector('.text-container[data-template="{template_name}"]');
            this.lines = document.querySelectorAll('.text-line');
            this.setupAnimations();
        },
        
        setupAnimations: function() {
            // Your animation setup logic
        },
        
        animateLine: function(lineIndex, timing) {
            // Your line animation logic
        },
        
        cleanup: function() {
            // Cleanup when animation ends
        }
    };
    """

# Update the deployment mapping
def deploy_display_plugins(self):
    # Add your plugin to the deployment list
    plugins = {
        # ... existing plugins
        '{template_name}_display': self._get_{template_name}_display_plugin_js()
    }
```

### Phase 6: Configuration Setup

#### 6.1 Create YAML Configuration
```yaml
# config/{template_name}.yaml
template_name: "{template_name}"
category: "{category}"

# Animation parameters
animation:
  duration_ms: 15000
  delay_between_lines_ms: 500
  
# Presets for different use cases
presets:
  default:
    title: "Default {Template} Animation"
    animation:
      duration_ms: 10000
      
  fast:
    title: "Fast {Template} Animation"
    animation:
      duration_ms: 5000
      
  slow:
    title: "Slow {Template} Animation"
    animation:
      duration_ms: 20000
```

### Phase 7: Integration and Testing

#### 7.1 Update Hierarchical Template Converter
```python
# src/scrollcast/conversion/hierarchical_template_converter.py
# Add your converter to the mapping

from .{template_name}_plugin_converter import {TemplateName}PluginConverter

class HierarchicalTemplateConverter:
    def __init__(self):
        self.converters = {
            # ... existing converters
            "{template_name}": {TemplateName}PluginConverter,
        }
```

#### 7.2 Test with Integration Script
```bash
# Test your template
./test/orchestrator_demo.sh {template_name} default test/sample_eng.txt test_output

# Verify external assets are deployed
ls contents/html/assets/{template_name}-display-plugin.js
ls contents/html/templates/{category}/{template_name}/

# Test with integration_test.sh
./test/integration_test.sh
```

### Phase 8: Validation and Quality Assurance

#### 8.1 Verification Checklist
- [ ] HTML follows unified CSS class structure
- [ ] External JavaScript architecture implemented
- [ ] CSS follows naming standards
- [ ] All abstract methods implemented
- [ ] Configuration file created
- [ ] Integration test passes
- [ ] Assets deployed correctly
- [ ] Animation timing works
- [ ] Mobile responsive
- [ ] No conflicts with other templates

#### 8.2 Critical Architecture Constraints

**ABSOLUTE REQUIREMENTS - VIOLATIONS WILL BREAK EXISTING TEMPLATES**:

1. **ISOLATED IMPLEMENTATION ONLY**:
   - ❌ **NEVER** modify existing template converters
   - ❌ **NEVER** modify existing template HTML/CSS/JS files
   - ❌ **NEVER** change core conversion logic that affects existing templates
   - ✅ **ONLY** add new files in new directories
   - ✅ **ONLY** add new entries to mappings (do not modify existing entries)

2. **HIERARCHICAL TEMPLATE CONVERTER ISOLATION**:
   ```python
   # WRONG - This breaks existing templates by changing core logic
   def convert_ass_to_html(self, ass_file_path: str, html_output_path: str):
       # Modifying existing conversion logic
       
   # RIGHT - Only add new template mapping
   self.template_mapping = {
       "existing_template": {...},  # DO NOT TOUCH
       "new_template": {...}        # ONLY ADD NEW
   }
   ```

3. **FILE_DEPLOYER ISOLATION**:
   ```python
   # WRONG - Changing existing plugin logic
   def _get_existing_plugin_js(self):
       # Modifying existing plugin
       
   # RIGHT - Only add new plugin method
   def _get_new_template_display_plugin_js(self):
       # New plugin only
       
   # Update plugin mapping - ADD ONLY, don't modify existing
   plugins = {
       "existing_plugin": self._get_existing_plugin_js(),  # DO NOT TOUCH
       "new_plugin": self._get_new_template_display_plugin_js()  # ADD ONLY
   }
   ```

4. **TEST SCRIPT ISOLATION**:
   - ❌ **NEVER** modify case statements for existing templates
   - ❌ **NEVER** change existing template paths or settings
   - ✅ **ONLY** add new case for new template

**VERIFICATION REQUIREMENTS**:
```bash
# BEFORE any implementation - check git status
git status --porcelain
# Should be clean or only show new files

# AFTER implementation - verify no existing files modified
git status --porcelain
# Should ONLY show new files, NEVER modified existing files

# If ANY existing files are modified, STOP and rollback immediately
git checkout HEAD -- <modified_existing_file>
```

#### 8.3 Why These Constraints Exist

**Root Cause of Template Corruption**:
- ScrollCast uses a **shared conversion pipeline** 
- Modifying core converters affects ALL templates
- HTML files are **regenerated** when core logic changes
- Existing demo files get **overwritten** with new generation logic

**The Template Regeneration Problem**:
```
User adds new template → Modifies HierarchicalTemplateConverter
→ Core conversion logic changes → ALL templates regenerate
→ Existing demo HTML files overwritten → Templates broken
```

**Correct Isolation Pattern**:
```
User adds new template → ONLY adds new mapping entry
→ Core logic unchanged → Only new template generates
→ Existing templates unaffected → System stable
```

#### 8.4 Anti-Pattern Detection

**Red Flags That Indicate You're Breaking Existing Templates**:
- Modifying any existing `.py` files beyond adding new mapping entries
- Changing logic in `convert_ass_to_html()` or `generate_html()` methods
- Updating existing plugin JavaScript generation
- Modifying existing template case statements
- Any change that affects the "how" of HTML generation vs "what" template to use

**Safe Pattern Recognition**:
- Adding new files only
- Adding new mapping/dictionary entries only  
- Creating new plugin methods (not modifying existing ones)
- New configuration files
- New directories under appropriate categories

#### 8.5 Common Pitfalls to Avoid

**DO NOT**:
- ❌ Generate HTML programmatically in converter
- ❌ Include inline JavaScript/CSS
- ❌ **Break existing template functionality (CRITICAL)**
- ❌ **Modify existing template converters (CRITICAL)**
- ❌ **Change core conversion logic (CRITICAL)**
- ❌ Use template-specific class names without template prefix
- ❌ Hardcode asset paths
- ❌ Skip abstract method implementation
- ❌ Ignore CSS Override Architecture requirements

**DO**:
- ✅ Use template-based HTML generation
- ✅ Follow external asset architecture
- ✅ Use unified CSS classes
- ✅ Implement all abstract methods
- ✅ **Test that existing templates still work (CRITICAL)**
- ✅ **Verify no existing files are modified (CRITICAL)**
- ✅ Follow CSS naming standards
- ✅ Support decoration system integration

## Lessons Learned from Implementation Failures

### horizontal_ticker Failure Analysis
**What Went Wrong**:
1. **Architecture Violation**: Generated HTML programmatically instead of using template files
2. **Asset Architecture Ignored**: Did not follow external JavaScript reference architecture
3. **CSS Class Inconsistency**: Used template-specific classes without unified structure
4. **Integration Workflow Ignored**: Did not work with integration_test.sh
5. **Decoration System Conflicts**: Broke existing template functionality

### vertical_drop Failure Analysis
**What Went Wrong**:
1. **Isolation Violation**: Modified existing template converter methods instead of only adding new mappings
2. **Core Logic Modification**: Changed shared conversion pipeline affecting ALL templates
3. **HTML Regeneration**: Caused existing demo HTML files to be overwritten and corrupted
4. **Shared State Corruption**: Changes to HierarchicalTemplateConverter affected template rendering logic for all templates

**Critical Insight**: Even following the horizontal_ticker lessons was insufficient because the guide failed to emphasize the **ISOLATION PRINCIPLE** - that any modification to shared/core files will trigger regeneration and corruption of existing templates.

### Root Cause: Shared Conversion Pipeline
The fundamental issue is that scroll-cast uses a **single shared conversion pipeline**:
```
Template Request → HierarchicalTemplateConverter → Core Logic → HTML Generation
```

When you modify ANY part of the core logic (even just adding a mapping), if not done correctly, it can trigger regeneration of ALL templates, overwriting existing demo files with new generation logic.

### Key Success Factors (Updated)
1. **Absolute Isolation**: ONLY add new files and new mapping entries
2. **No Core Logic Changes**: Never modify existing conversion methods
3. **Verification-First**: Check `git status` before and after every change
4. **Template-First Approach**: HTML template is source of truth
5. **External Asset Deployment**: JavaScript/CSS deployed as external files
6. **Unified CSS Classes**: Follow `.text-container[data-template]` + `.text-line` pattern
7. **PluginConverterBase Compliance**: Implement ALL abstract methods
8. **Integration Testing**: Must work with existing test infrastructure
9. **Rollback Readiness**: Be prepared to completely rollback if ANY existing file is modified

## Templates Architecture Summary

```
Template Addition Flow:
1. Plan architecture → 2. Create file structure → 3. Implement HTML template
4. Implement converter → 5. Update asset deployment → 6. Create configuration
7. Update hierarchical converter → 8. Test integration → 9. Validate quality

Success Criteria:
- Works with integration_test.sh
- Follows external asset architecture  
- Uses unified CSS classes
- Implements all abstract methods
- No conflicts with existing templates
```

This guide ensures that future template additions follow the established architecture and avoid the critical mistakes that led to the horizontal_ticker implementation failure.