#!/bin/bash

# scroll-cast HTML Generator with Configuration System
# Usage: ./test/orchestrator_demo.sh [template] [preset] [input_file] [filename] [output_dir]
#
# Arguments:
#   template    - Template to use (default: typewriter_fade)
#   preset      - Preset to use (optional)
#   input_file  - Input text file (default: test/sample_eng.txt)  
#   filename    - Output filename without extension (default: auto-generated)
#   output_dir  - Base output directory (default: output-default)
#
# Output paths:
#   HTML: {output_dir}/web/{filename}.html
#   ASS:  {output_dir}/ass/{filename}.ass (intermediate file)

# デフォルト値
TEMPLATE=${1:-"typewriter_fade"}
PRESET=${2:-""}  # プリセットは未指定でもOK
INPUT_FILE=${3:-"test/sample_eng.txt"}
BASE_OUTPUT_DIR=${5:-"output-default"}

# 出力ファイル名の設定（拡張子なし、パスなし）
if [ -n "$4" ]; then
    # 4番目の引数からパスと拡張子を除去してファイル名のみ取得
    OUTPUT_BASE=$(basename "$4" .html)
    OUTPUT_BASE=$(basename "$OUTPUT_BASE" .ass)
else
    # デフォルト: テンプレート名_プリセット名
    if [ -n "$PRESET" ]; then
        OUTPUT_BASE="${TEMPLATE}_${PRESET}"
    else
        # プリセット未指定時はdefaultプリセットを使用
        OUTPUT_BASE="${TEMPLATE}_default"
    fi
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
    echo "  preset       Preset to use (optional)"
    echo "               Available presets by template:"
    echo "                 typewriter_fade: fast, slow, cinematic, dramatic, subtle, presentation"
    echo "                 railway_scroll: express, local, limited_express, announcement, news_ticker, elegant"
    echo "                 simple_role: credits, news, announcement, fast_scroll, slow_scroll, presentation"
    echo "                 revolver_up: default, fast, slow, compact, elegant, presentation"
    echo "  input_file   Input text file (default: test/sample_eng.txt)"
    echo "  filename     Output filename without extension (default: auto-generated)"
    echo "  output_dir   Base output directory (default: output-default)"
    echo
    echo "Output paths:"
    echo "  🌐 HTML: {output_dir}/web/{filename}.html"
    echo "  📝 ASS:  {output_dir}/ass/{filename}.ass (intermediate)"
    echo
    echo "Examples:"
    echo "  $0                                        # typewriter_fade_default"
    echo "  $0 typewriter_fade fast                   # typewriter_fade_fast"
    echo "  $0 railway_scroll express test/sample_eng.txt  # railway_scroll_express"
    echo "  $0 typewriter_fade dramatic test/sample_eng.txt my_demo  # my_demo"
    echo
    exit 0
fi

# 出力先をベースディレクトリに基づいて設定
OUTPUT_HTML="$BASE_OUTPUT_DIR/web/${OUTPUT_BASE}.html"
ASS_OUTPUT="$BASE_OUTPUT_DIR/ass/${OUTPUT_BASE}.ass"

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
mkdir -p "$BASE_OUTPUT_DIR/web" "$BASE_OUTPUT_DIR/ass"

print_status "INFO" "Generating scroll-cast HTML with Configuration System..."
echo "   Template: $TEMPLATE"
echo "   Preset: $PRESET"
echo "   Input: $INPUT_FILE"
echo "   HTML Output: $OUTPUT_HTML"
echo "   ASS Intermediate: $ASS_OUTPUT"
echo

# テンプレート名の設定（オーケストレーターが設定ファイルを自動解決）
case $TEMPLATE in
    "typewriter_fade")
        TEMPLATE_NAME="typewriter_fade"
        ;;
    "railway_scroll") 
        TEMPLATE_NAME="railway_scroll"
        ;;
    "simple_role")
        TEMPLATE_NAME="simple_role"
        ;;
    "revolver_up")
        TEMPLATE_NAME="revolver_up"
        ;;
    "typewriter_pop")
        TEMPLATE_NAME="typewriter_pop"
        ;;    "typewriter_fill_screen")
        TEMPLATE_NAME="typewriter_fill_screen"
        ;;

    *)
        print_status "FAIL" "Unknown template: $TEMPLATE"
        exit 1
        ;;
esac

# Step 1: Generate files using orchestrator system
print_status "INFO" "Step 1: Generating ASS and HTML files using orchestrator system..."

if [ "$USE_MOCK" = "false" ]; then
    # プリセット指定の組み立て
    PRESET_OPTION=""
    if [ -n "$PRESET" ]; then
        PRESET_OPTION="--preset $PRESET"
    fi
    
    # Try using scroll-cast orchestrator
    PYTHONPATH=src python3 -m scrollcast.orchestrator.cli.main \
        "$TEMPLATE_NAME" \
        "$(cat "$INPUT_FILE")" \
        --output "$OUTPUT_HTML" \
        --ass-output "$ASS_OUTPUT" \
        $PRESET_OPTION \
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
    generate_mock_html "$TEMPLATE" "$PRESET" "$INPUT_FILE" "$OUTPUT_HTML"
fi

# 結果確認
if [ $? -eq 0 ] && [ -f "$OUTPUT_HTML" ]; then
    echo
    print_status "PASS" "scroll-cast HTML generation completed successfully!"
    echo "   Template: $TEMPLATE"
    if [ -n "$PRESET" ]; then
        echo "   Preset: $PRESET"
    fi
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
    echo
    echo "💡 Next steps:"
    echo "   - Open $OUTPUT_HTML in your browser"
    echo "   - Test different presets with --preset option"
    echo "   - Compare with original subtitle-generator output"
    echo
    echo "🎛️ Try other presets for $TEMPLATE:"
    echo "   $0 $TEMPLATE fast $INPUT_FILE"
    echo "   $0 $TEMPLATE slow $INPUT_FILE"
    echo "   $0 $TEMPLATE cinematic $INPUT_FILE"
else
    echo
    print_status "FAIL" "scroll-cast HTML generation failed"
    exit 1
fi