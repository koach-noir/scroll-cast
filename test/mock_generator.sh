#!/bin/bash

# Mock Generation System for scroll-cast
# Fallback generation when orchestrator is unavailable
# Usage: source mock_generator.sh

# Mock ASS generation function
generate_mock_ass() {
    local input_file="$1"
    local output_file="$2"
    local template_name="$3"
    
    print_status "INFO" "Using mock ASS generation"
    
    # Read input text for mock processing
    local input_text=$(cat "$input_file")
    
    cat > "$output_file" << EOF
[Script Info]
Title: scroll-cast $template_name
ScriptType: v4.00+

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,Arial,64,&H00FFFFFF,&H000000FF,&H00000000,&H80000000,1,0,0,0,100,100,0,0,1,2,0,2,10,10,10,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
EOF

    # Add dialogue entries from input text
    local start_time=0
    local duration=3
    
    echo "$input_text" | while IFS= read -r line; do
        if [ -n "$line" ]; then
            local start_formatted=$(printf "%d:%02d:%02d.%02d" $((start_time / 3600)) $(((start_time % 3600) / 60)) $((start_time % 60)) 0)
            local end_time=$((start_time + duration))
            local end_formatted=$(printf "%d:%02d:%02d.%02d" $((end_time / 3600)) $(((end_time % 3600) / 60)) $((end_time % 60)) 0)
            
            echo "Dialogue: 0,$start_formatted,$end_formatted,Default,,0,0,0,,$line" >> "$output_file"
            start_time=$((start_time + duration + 1))
        fi
    done
    
    print_status "INFO" "Mock ASS file created"
}

# Get template configuration for mock HTML generation
get_template_config() {
    local template="$1"
    
    case $template in
        "typewriter_fade")
            echo "typewriter_fade typewriter_fade.css typewriter_fade.js typewriter-container typewriter-char ../templates/$template"
            ;;
        "railway_scroll")
            echo "railway_scroll railway_scroll.css railway_scroll.js railway-container railway-line ../templates/$template"
            ;;
        "simple_role")
            echo "scroll_role scroll_role.css scroll_role.js scroll-container scroll-line ../templates/$template"
            ;;
        "revolver_up")
            echo "revolver_up sc-template.css sc-template.js text-container text-line ../templates/scroll"
            ;;
        *)
            echo "typewriter_fade typewriter_fade.css typewriter_fade.js typewriter-container typewriter-char ../templates"
            ;;
    esac
}

# Deploy template assets for specific templates
deploy_mock_assets() {
    local template="$1"
    
    if [ "$template" = "revolver_up" ]; then
        python3 -c "
import sys
sys.path.append('src')
from scrollcast.deployment.file_deployer import FileDeployer
deployer = FileDeployer()
deployer.sync_template_assets('contents/html', 'scroll', 'revolver_up')
print('✅ revolver_up assets deployed')
" 2>/dev/null || echo "⚠️ Asset deployment skipped"
    fi
}

# Generate content HTML based on template type
generate_template_content() {
    local template="$1"
    local input_text="$2"
    local output_file="$3"
    local element_class="$4"
    
    case $template in
        "typewriter_fade")
            echo '        <div class="typewriter-sentence active">' >> "$output_file"
            echo "$input_text" | while IFS= read -r line; do
                if [ -n "$line" ]; then
                    for (( i=0; i<${#line}; i++ )); do
                        char="${line:$i:1}"
                        echo "            <span class=\"typewriter-char\">$char</span>" >> "$output_file"
                    done
                fi
            done
            echo '        </div>' >> "$output_file"
            ;;
        "revolver_up")
            echo '    <div class="revolver-viewport">' >> "$output_file"
            local line_index=0
            echo "$input_text" | while IFS= read -r line; do
                if [ -n "$line" ]; then
                    echo "        <div class=\"text-line\" data-line=\"$line_index\" data-char-count=\"${#line}\">$line</div>" >> "$output_file"
                    line_index=$((line_index + 1))
                fi
            done
            echo '    </div>' >> "$output_file"
            ;;
        *)
            echo "$input_text" | while IFS= read -r line; do
                if [ -n "$line" ]; then
                    echo "        <div class=\"$element_class\">$line</div>" >> "$output_file"
                fi
            done
            ;;
    esac
}

# Generate mock HTML file
generate_mock_html() {
    local template="$1"
    local preset="$2"
    local input_file="$3"
    local output_file="$4"
    local config_file="$5"
    
    print_status "INFO" "Using mock HTML generation"
    
    # Deploy template assets if needed
    deploy_mock_assets "$template"
    
    # Get template configuration
    local config=($(get_template_config "$template"))
    local template_path="${config[0]}"
    local css_file="${config[1]}"
    local js_file="${config[2]}"
    local container_class="${config[3]}"
    local element_class="${config[4]}"
    local css_path_prefix="${config[5]}"
    
    # Read input text
    local input_text=$(cat "$input_file")
    
    # Generate HTML header
    cat > "$output_file" << EOF
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>scroll-cast: $template (preset: $preset)</title>
    <link rel="stylesheet" href="$css_path_prefix/$template_path/$css_file">
</head>
<body>
    <div class="$container_class">
EOF

    # Generate template-specific content
    generate_template_content "$template" "$input_text" "$output_file" "$element_class"

    # Generate HTML footer with configuration
    cat >> "$output_file" << EOF
    </div>
    
    <!-- Configuration data from $config_file preset: $preset -->
    <script>
        window.scrollcastConfig = {
            template: '$template',
            preset: '$preset',
            configFile: '$config_file'
        };
    </script>
    
EOF

    # Generate script tag with correct path
    if [ "$template" = "revolver_up" ]; then
        echo "    <script src=\"$css_path_prefix/$template_path/$js_file\"></script>" >> "$output_file"
    else
        echo "    <script src=\"../templates/$template/$template_path/$js_file\"></script>" >> "$output_file"
    fi

    # Generate auto-start script
    cat >> "$output_file" << 'EOF'
    <script>
        // Auto-start animation with configuration
        window.addEventListener('load', function() {
            console.log('Page loaded with config:', window.scrollcastConfig);
            if (typeof startAnimation === 'function') {
                startAnimation();
            } else if (typeof initializeTypewriter === 'function') {
                initializeTypewriter();
            } else if (typeof initializeRailway === 'function') {
                initializeRailway();
            } else if (typeof initializeScroll === 'function') {
                initializeScroll();
            } else {
                console.log('No animation function found - manual start may be required');
            }
        });
    </script>
</body>
</html>
EOF
    
    print_status "INFO" "Mock HTML file created with configuration info"
}

# Check if this script is being sourced
if [ "${BASH_SOURCE[0]}" != "${0}" ]; then
    # Script is being sourced
    print_status() {
        local status=$1
        local message=$2
        case $status in
            "PASS") echo -e "${GREEN}✅ PASS${NC}: $message" ;;
            "FAIL") echo -e "${RED}❌ FAIL${NC}: $message" ;;
            "INFO") echo -e "${BLUE}ℹ️  INFO${NC}: $message" ;;
            "WARN") echo -e "${YELLOW}⚠️  WARN${NC}: $message" ;;
        esac
    }
    
    # Define colors if not already defined
    RED=${RED:-'\033[0;31m'}
    GREEN=${GREEN:-'\033[0;32m'}
    YELLOW=${YELLOW:-'\033[1;33m'}
    BLUE=${BLUE:-'\033[0;34m'}
    NC=${NC:-'\033[0m'}
fi