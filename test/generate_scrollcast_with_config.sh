#!/bin/bash

# scroll-cast HTML Generator with Configuration System
# Usage: ./test/generate_scrollcast_with_config.sh [template] [preset] [input_file] [filename]
#
# Arguments:
#   template    - Template to use (default: typewriter)
#   preset      - Preset to use (default: default)
#   input_file  - Input text file (default: test/sample_eng.txt)  
#   filename    - Output filename without extension (default: auto-generated)
#
# Output paths are fixed:
#   HTML: test/output/{filename}.html
#   ASS:  test/output/ass/{filename}.ass (intermediate file)

# デフォルト値
TEMPLATE=${1:-"typewriter_fade"}
PRESET=${2:-"cinematic"}
INPUT_FILE=${3:-"test/sample_eng.txt"}

# 出力ファイル名の設定（拡張子なし、パスなし）
if [ -n "$4" ]; then
    # 4番目の引数からパスと拡張子を除去してファイル名のみ取得
    OUTPUT_BASE=$(basename "$4" .html)
    OUTPUT_BASE=$(basename "$OUTPUT_BASE" .ass)
else
    # デフォルト: テンプレート名、プリセット名、入力ファイル名から生成
    INPUT_BASE=$(basename "$INPUT_FILE" .txt)
    OUTPUT_BASE="${TEMPLATE}_${PRESET}_${INPUT_BASE}"
fi

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
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

# ヘルプ表示
if [ "$1" = "-h" ] || [ "$1" = "--help" ]; then
    echo "🌐 scroll-cast HTML Generator with Configuration System"
    echo
    echo "Usage: $0 [template] [preset] [input_file] [filename]"
    echo
    echo "Arguments:"
    echo "  template     Template to use (default: typewriter_fade)"
    echo "               Available: typewriter_fade, railway_scroll, simple_role"
    echo "  preset       Preset to use (default: cinematic)"
    echo "               Available presets by template:"
    echo "                 typewriter_fade: fast, slow, cinematic, dramatic, subtle, presentation"
    echo "                 railway_scroll: express, local, limited_express, announcement, news_ticker, elegant"
    echo "                 simple_role: credits, news, announcement, fast_scroll, slow_scroll, presentation"
    echo "  input_file   Input text file (default: test/sample_eng.txt)"
    echo "  filename     Output filename without extension (default: auto-generated)"
    echo
    echo "Output paths (fixed):"
    echo "  🌐 HTML: contents/html/{filename}.html"
    echo "  📝 ASS:  contents/ass/{filename}.ass (intermediate)"
    echo
    echo "Examples:"
    echo "  $0                                        # typewriter_fade_cinematic_sample_eng"
    echo "  $0 typewriter_fade fast                 # typewriter_fade_fast_sample_eng"
    echo "  $0 railway_scroll express test/sample_eng.txt  # railway_scroll_express_sample_eng"
    echo "  $0 typewriter_fade dramatic test/sample_eng.txt my_demo  # my_demo"
    echo
    exit 0
fi

# 出力先を contents/html と contents/ass フォルダに分離
OUTPUT_HTML="contents/html/${OUTPUT_BASE}.html"
ASS_OUTPUT="contents/ass/${OUTPUT_BASE}.ass"

# 入力ファイルの存在確認
if [ ! -f "$INPUT_FILE" ]; then
    print_status "FAIL" "Input file '$INPUT_FILE' not found"
    exit 1
fi

# 設定システムの確認
if [ ! -f "src/scrollcast/__init__.py" ]; then
    print_status "FAIL" "scroll-cast module not found"
    print_status "INFO" "Using mock generation instead"
    USE_MOCK=true
else
    USE_MOCK=false
fi

# 出力フォルダの作成（存在しない場合）
mkdir -p "contents/html" "contents/ass"

print_status "INFO" "Generating scroll-cast HTML with Configuration System..."
echo "   Template: $TEMPLATE"
echo "   Preset: $PRESET"
echo "   Input: $INPUT_FILE"
echo "   HTML Output: $OUTPUT_HTML"
echo "   ASS Intermediate: $ASS_OUTPUT"
echo

# 設定ファイルのマッピング
CONFIG_FILE=""
case $TEMPLATE in
    "typewriter_fade")
        CONFIG_FILE="config/typewriter_fade.yaml"
        TEMPLATE_NAME="typewriter_fade"
        ;;
    "railway_scroll") 
        CONFIG_FILE="config/railway_scroll.yaml"
        TEMPLATE_NAME="railway_scroll"
        ;;
    "simple_role")
        CONFIG_FILE="config/simple_role.yaml"
        TEMPLATE_NAME="simple_role"
        ;;
    *)
        print_status "FAIL" "Unknown template: $TEMPLATE"
        exit 1
        ;;
esac

if [ ! -f "$CONFIG_FILE" ]; then
    print_status "FAIL" "Configuration file not found: $CONFIG_FILE"
    exit 1
fi

# Step 1: Generate ASS file using configuration system
print_status "INFO" "Step 1: Generating ASS file with configuration system..."

if [ "$USE_MOCK" = "false" ]; then
    # Try using scroll-cast Python module with configuration
    python3 -c "
import sys
sys.path.append('src')

try:
    from scrollcast.config.config_loader import ConfigLoader
    from scrollcast.boxing.display_config import DisplayConfig
    from scrollcast.boxing.text_formatter import TextFormatter
    
    # Template class import based on template name
    if '$TEMPLATE_NAME' == 'typewriter_fade':
        from scrollcast.coloring.typewriter_fade import TypewriterFadeTemplate
        template_class = TypewriterFadeTemplate
    elif '$TEMPLATE_NAME' == 'railway_scroll':
        from scrollcast.coloring.railway_scroll import RailwayScrollTemplate
        template_class = RailwayScrollTemplate
    elif '$TEMPLATE_NAME' == 'simple_role':
        from scrollcast.coloring.simple_role import SimpleRoleTemplate
        template_class = SimpleRoleTemplate
    else:
        print(f'❌ Unknown template: $TEMPLATE_NAME')
        sys.exit(1)
    
    # Read input text
    with open('$INPUT_FILE', 'r', encoding='utf-8') as f:
        text = f.read()
    
    # Configuration loader and template
    config_dir = 'config'
    loader = ConfigLoader(config_dir)
    template = template_class()
    
    # Create parameters from config and preset
    params = loader.create_parameters_from_config('$TEMPLATE_NAME', '$PRESET')
    if not params:
        print('❌ Failed to create parameters from config')
        # Use default parameters as fallback
        param_dict = {
            'char_interval': 0.15,
            'fade_duration': 0.1,
            'font_size': 36,
            'font_name': 'Arial',
            'pause_duration': 1.0,
            'pause_between_lines': 1.0,
            'pause_between_paragraphs': 2.0
        }
    else:
        param_dict = params.model_dump()
        print(f'✅ Parameters loaded for preset \\"$PRESET\\":')
        for key, value in param_dict.items():
            print(f'   {key}: {value}')
    
    # Create FormattedText
    config = DisplayConfig.create_mobile_portrait(font_size=param_dict.get('font_size', 48))
    formatter = TextFormatter(config)
    formatted_text = formatter.format_for_display(text)
    
    # Generate ASS
    ass_content = template.generate_ass_from_formatted(formatted_text, **param_dict)
    duration = template.calculate_total_duration(formatted_text, **param_dict)
    
    print(f'✅ ASS content generated: {len(ass_content)} characters, {duration:.2f}s duration')
    
    # Save ASS
    with open('$ASS_OUTPUT', 'w', encoding='utf-8') as f:
        f.write(ass_content)
    
    print(f'✅ ASS file saved: $ASS_OUTPUT')
    
except ImportError as e:
    print(f'❌ Import error: {e}')
    print('🔄 Falling back to mock generation...')
    sys.exit(1)
except Exception as e:
    print(f'❌ Error during ASS generation: {e}')
    print('🔄 Falling back to mock generation...')
    sys.exit(1)
"

    if [ $? -ne 0 ]; then
        print_status "WARN" "Python module generation failed, using mock generation"
        USE_MOCK=true
    fi
fi

if [ "$USE_MOCK" = "true" ]; then
    # Mock ASS generation
    print_status "INFO" "Using mock ASS generation"
    
    # Read input text for mock processing
    INPUT_TEXT=$(cat "$INPUT_FILE")
    
    cat > "$ASS_OUTPUT" << EOF
[Script Info]
Title: scroll-cast $TEMPLATE_NAME
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
    
    echo "$INPUT_TEXT" | while IFS= read -r line; do
        if [ -n "$line" ]; then
            local start_formatted=$(printf "%d:%02d:%02d.%02d" $((start_time / 3600)) $(((start_time % 3600) / 60)) $((start_time % 60)) 0)
            local end_time=$((start_time + duration))
            local end_formatted=$(printf "%d:%02d:%02d.%02d" $((end_time / 3600)) $(((end_time % 3600) / 60)) $((end_time % 60)) 0)
            
            echo "Dialogue: 0,$start_formatted,$end_formatted,Default,,0,0,0,,$line" >> "$ASS_OUTPUT"
            start_time=$((start_time + duration + 1))
        fi
    done
    
    print_status "INFO" "Mock ASS file created"
fi

# ASS ファイルの確認
if [ -f "$ASS_OUTPUT" ]; then
    print_status "PASS" "ASS generated: $ASS_OUTPUT"
else
    print_status "FAIL" "ASS file not found: $ASS_OUTPUT"
    exit 1
fi

# Step 2: Convert ASS to HTML using template system
print_status "INFO" "Step 2: Converting ASS to HTML with template system..."

if [ "$USE_MOCK" = "false" ]; then
    # Try using scroll-cast conversion system
    python3 -c "
import sys
sys.path.append('src')

try:
    from scrollcast.conversion.hierarchical_template_converter import HierarchicalTemplateConverter
    
    converter = HierarchicalTemplateConverter('$TEMPLATE')
    converter.convert_ass_to_html('$ASS_OUTPUT', '$OUTPUT_HTML')
    print('✅ Template conversion completed')
    
except ImportError:
    print('❌ Conversion module not found, using mock HTML generation')
    sys.exit(1)
except Exception as e:
    print(f'❌ Template conversion failed: {e}')
    print('🔄 Falling back to mock HTML generation...')
    sys.exit(1)
"

    if [ $? -ne 0 ]; then
        print_status "WARN" "Python conversion failed, using mock HTML generation"
        USE_MOCK=true
    fi
fi

if [ "$USE_MOCK" = "true" ]; then
    # Mock HTML generation
    print_status "INFO" "Using mock HTML generation"
    
    # Determine template-specific paths and settings
    template_path="typewriter_fade"
    css_file="typewriter_fade.css"
    js_file="typewriter_fade.js"
    container_class="typewriter-container"
    element_class="typewriter-char"
    
    case $TEMPLATE in
        "typewriter_fade")
            template_path="typewriter_fade"
            css_file="typewriter_fade.css"
            js_file="typewriter_fade.js"
            container_class="typewriter-container"
            element_class="typewriter-char"
            ;;
        "railway_scroll")
            template_path="railway_scroll"
            css_file="railway_scroll.css"
            js_file="railway_scroll.js"
            container_class="railway-container"
            element_class="railway-line"
            ;;
        "simple_role")
            template_path="scroll_role"
            css_file="scroll_role.css"
            js_file="scroll_role.js"
            container_class="scroll-container"
            element_class="scroll-line"
            ;;
    esac
    
    # Generate HTML using mock system
    INPUT_TEXT=$(cat "$INPUT_FILE")
    
    cat > "$OUTPUT_HTML" << EOF
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>scroll-cast: $TEMPLATE (preset: $PRESET)</title>
    <link rel="stylesheet" href="../templates/$TEMPLATE/$template_path/$css_file">
</head>
<body>
    <div class="$container_class">
EOF

    # Generate appropriate content structure based on template
    if [ "$TEMPLATE" = "typewriter_fade" ]; then
        echo '        <div class="typewriter-sentence active">' >> "$OUTPUT_HTML"
        echo "$INPUT_TEXT" | while IFS= read -r line; do
            if [ -n "$line" ]; then
                for (( i=0; i<${#line}; i++ )); do
                    char="${line:$i:1}"
                    echo "            <span class=\"typewriter-char\">$char</span>" >> "$OUTPUT_HTML"
                done
            fi
        done
        echo '        </div>' >> "$OUTPUT_HTML"
    else
        echo "$INPUT_TEXT" | while IFS= read -r line; do
            if [ -n "$line" ]; then
                echo "        <div class=\"$element_class\">$line</div>" >> "$OUTPUT_HTML"
            fi
        done
    fi

    cat >> "$OUTPUT_HTML" << EOF
    </div>
    
    <!-- Configuration data from $CONFIG_FILE preset: $PRESET -->
    <script>
        window.scrollcastConfig = {
            template: '$TEMPLATE',
            preset: '$PRESET',
            configFile: '$CONFIG_FILE'
        };
    </script>
    
    <script src="../templates/$TEMPLATE/$template_path/$js_file"></script>
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
fi

# 結果確認
if [ $? -eq 0 ] && [ -f "$OUTPUT_HTML" ]; then
    echo
    print_status "PASS" "scroll-cast HTML generation completed successfully!"
    echo "   Template: $TEMPLATE"
    echo "   Preset: $PRESET"
    echo "   Config: $CONFIG_FILE"
    echo "   HTML file: $OUTPUT_HTML"
    echo "   ASS file: $ASS_OUTPUT"
    
    # HTMLファイルの統計情報
    SENTENCES=$(grep -c 'typewriter-sentence\|sentence\|dialogue\|railway-line\|scroll-line' "$OUTPUT_HTML" 2>/dev/null || echo "0")
    FILE_SIZE=$(wc -c < "$OUTPUT_HTML")
    echo "   Elements: $SENTENCES"
    echo "   File size: $FILE_SIZE bytes"
    
    # ASSファイルの統計情報
    DIALOGUE_COUNT=$(grep -c "^Dialogue:" "$ASS_OUTPUT" 2>/dev/null || echo "0")
    echo "   ASS dialogues: $DIALOGUE_COUNT"
    
    # フォルダごとのサマリー
    echo
    echo "📁 Output Summary:"
    echo "   🌐 HTML: $OUTPUT_HTML"
    echo "   📝 ASS: $ASS_OUTPUT"
    echo "   ⚙️ Config: $CONFIG_FILE"
    echo
    echo "💡 Next steps:"
    echo "   - Open $OUTPUT_HTML in your browser"
    echo "   - Test different presets from $CONFIG_FILE"
    echo "   - Compare with original subtitle-generator output"
    echo
    echo "🎛️ Try other presets for $TEMPLATE:"
    
    # Extract available presets from config file
    if [ -f "$CONFIG_FILE" ]; then
        AVAILABLE_PRESETS=$(grep -A 100 "presets:" "$CONFIG_FILE" | grep "^\s*-\s*name:" | sed 's/.*name:\s*//' | tr -d '"' | tr -d "'" | head -5 | tr '\n' ' ')
        if [ -n "$AVAILABLE_PRESETS" ]; then
            for preset in $AVAILABLE_PRESETS; do
                echo "   $0 $TEMPLATE $preset $INPUT_FILE"
            done
        fi
    fi
else
    echo
    print_status "FAIL" "scroll-cast HTML generation failed"
    exit 1
fi