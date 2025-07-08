#!/bin/bash

# scroll-cast HTML Generator with Configuration System
# Usage: ./test/orchestrator_demo.sh [template] [preset] [input_file] [filename]
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
    echo "               Available: typewriter_fade, railway_scroll, simple_role, revolver_up"
    echo "  preset       Preset to use (default: cinematic)"
    echo "               Available presets by template:"
    echo "                 typewriter_fade: fast, slow, cinematic, dramatic, subtle, presentation"
    echo "                 railway_scroll: express, local, limited_express, announcement, news_ticker, elegant"
    echo "                 simple_role: credits, news, announcement, fast_scroll, slow_scroll, presentation"
    echo "                 revolver_up: default, fast, slow, compact, elegant, presentation"
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
    "revolver_up")
        CONFIG_FILE="config/revolver_up.yaml"
        TEMPLATE_NAME="revolver_up"
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

# Step 1: Generate files using orchestrator system
print_status "INFO" "Step 1: Generating ASS and HTML files using orchestrator system..."

if [ "$USE_MOCK" = "false" ]; then
    # Try using scroll-cast orchestrator
    PYTHONPATH=src python3 -m scrollcast.orchestrator.cli.main \
        "$TEMPLATE_NAME" \
        "$(cat "$INPUT_FILE")" \
        --output "$OUTPUT_HTML" \
        --ass-output "$ASS_OUTPUT" \
        --preset "$PRESET" \
        --resolution 1080x1920 \
        2>&1 | while IFS= read -r line; do
            echo "   $line"
        done
    
    if [ $? -ne 0 ]; then
        print_status "WARN" "Orchestrator generation failed, using mock generation"
        USE_MOCK=true
    fi
fi

if [ "$USE_MOCK" = "true" ]; then
    # Load mock generation functions
    source "$(dirname "$0")/mock_generator.sh"
    
    # Generate mock ASS file
    generate_mock_ass "$INPUT_FILE" "$ASS_OUTPUT" "$TEMPLATE_NAME"
fi

# ASS ファイルの確認
if [ -f "$ASS_OUTPUT" ]; then
    print_status "PASS" "ASS generated: $ASS_OUTPUT"
else
    print_status "FAIL" "ASS file not found: $ASS_OUTPUT"
    exit 1
fi

# Step 2: Verify generated files (orchestrator already handles HTML conversion)
print_status "INFO" "Step 2: Verifying generated files..."

if [ "$USE_MOCK" = "false" ]; then
    # Files should already be generated by orchestrator
    if [ -f "$OUTPUT_HTML" ] && [ -f "$ASS_OUTPUT" ]; then
        print_status "PASS" "Orchestrator generated both files successfully"
    else
        print_status "WARN" "Orchestrator failed to generate files, using mock generation"
        USE_MOCK=true
    fi
fi

if [ "$USE_MOCK" = "true" ]; then
    # Load mock generation functions (already loaded above, but safe to call again)
    source "$(dirname "$0")/mock_generator.sh"
    
    # Generate mock HTML file
    generate_mock_html "$TEMPLATE" "$PRESET" "$INPUT_FILE" "$OUTPUT_HTML" "$CONFIG_FILE"
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