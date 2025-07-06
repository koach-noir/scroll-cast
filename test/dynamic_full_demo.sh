#!/bin/bash

# Dynamic Full Template Demo Script for scroll-cast
# YAMLファイルから自動的にテンプレート・プリセットを読み取り一括実行
# Usage: ./test/dynamic_full_demo.sh [input_file]

# デフォルト値
INPUT_FILE=${1:-"test/sample_eng.txt"}
OUTPUT_DIR="../contents"
CONFIG_DIR="config"

# ヘルプ表示
if [ "$1" = "-h" ] || [ "$1" = "--help" ]; then
    echo "🎬 Dynamic Full Template Demo Script for scroll-cast"
    echo
    echo "YAMLファイルから自動的に全テンプレート・プリセットを読み取り一括実行"
    echo
    echo "Usage: $0 [input_file]"
    echo
    echo "Arguments:"
    echo "  input_file   Input text file (default: test/sample_eng.txt)"
    echo
    echo "動的検出機能:"
    echo "  - $CONFIG_DIR/ から *.yaml ファイルを自動検出"
    echo "  - 各YAMLファイルから presets を自動抽出"
    echo "  - テンプレート・プリセット追加時の手動更新不要"
    echo
    echo "Output:"
    echo "  📁 Directory: $OUTPUT_DIR/"
    echo "  🌐 HTML files: demo_[template]_[preset].html"
    echo "  📝 ASS files:  demo_[template]_[preset].ass"
    echo
    exit 0
fi

# 入力ファイルの存在確認
if [ ! -f "$INPUT_FILE" ]; then
    echo "❌ Error: Input file '$INPUT_FILE' not found"
    exit 1
fi

# テストスクリプトの存在確認
if [ ! -f "./test/generate_scrollcast_with_config.sh" ]; then
    echo "❌ Error: './test/generate_scrollcast_with_config.sh' script not found"
    echo "Please run this script from the project root directory"
    exit 1
fi

# 設定ディレクトリの存在確認
if [ ! -d "$CONFIG_DIR" ]; then
    echo "❌ Error: Configuration directory '$CONFIG_DIR' not found"
    exit 1
fi

# 出力フォルダの作成
mkdir -p "$OUTPUT_DIR/html" "$OUTPUT_DIR/ass"

echo "🎬 Dynamic Full Template Demo - YAMLベース自動実行"
echo "   Input: $INPUT_FILE"
echo "   Config Directory: $CONFIG_DIR/"
echo "   Output Directory: $OUTPUT_DIR/"
echo

# 実行結果を記録する配列
declare -a RESULTS
declare -a DURATIONS
declare -a FILENAMES

# 実行時間計測関数
measure_time() {
    local start_time=$(date +%s)
    "$@" > /tmp/template_output.log 2>&1
    local exit_code=$?
    local end_time=$(date +%s)
    local duration=$((end_time - start_time))
    echo $duration
    return $exit_code
}

# YAMLファイルからテンプレート名を抽出する関数
extract_template_name() {
    local yaml_file="$1"
    grep "^template_name:" "$yaml_file" | sed 's/template_name: *//' | tr -d '"'
}

# YAMLファイルからプリセット名を抽出する関数
extract_preset_names() {
    local yaml_file="$1"
    # presetsセクション内のnameフィールドを抽出（両方の形式に対応）
    local names1=$(sed -n '/^presets:/,$p' "$yaml_file" | grep "^ *- name:" | sed 's/^ *- name: *//g' | sed 's/^"//g' | sed 's/"$//g')
    local names2=$(sed -n '/^presets:/,$p' "$yaml_file" | grep "^ *name:" | sed 's/^ *name: *//g' | sed 's/^"//g' | sed 's/"$//g')
    
    # 両方の結果を結合（重複除去）
    echo -e "$names1\n$names2" | grep -v "^$" | sort -u
}

# テンプレートとプリセットを動的に収集
echo "🔍 YAMLファイルから設定を動的読み込み中..."

declare -a template_preset_list
template_count=0
preset_total=0

for yaml_file in "$CONFIG_DIR"/*.yaml; do
    if [ -f "$yaml_file" ]; then
        template_name=$(extract_template_name "$yaml_file")
        
        # template_nameが有効な場合のみ処理
        if [ -n "$template_name" ] && [ "$template_name" != "null" ]; then
            preset_names=($(extract_preset_names "$yaml_file"))
            preset_count=${#preset_names[@]}
            
            if [ $preset_count -gt 0 ]; then
                echo "   📝 $template_name: $preset_count プリセット (${preset_names[*]})"
                ((template_count++))
                preset_total=$((preset_total + preset_count))
                
                # テンプレート・プリセット組み合わせをリストに追加
                for preset in "${preset_names[@]}"; do
                    template_preset_list+=("$template_name $preset")
                done
            else
                echo "   ⚠️  $template_name: プリセットが見つかりません"
            fi
        fi
    fi
done

total_count=${#template_preset_list[@]}

if [ $total_count -eq 0 ]; then
    echo "❌ Error: 有効なテンプレート・プリセットが見つかりませんでした"
    echo "   - $CONFIG_DIR/*.yaml ファイルを確認してください"
    echo "   - template_name と presets が正しく定義されているか確認してください"
    exit 1
fi

echo
echo "📊 検出結果:"
echo "   テンプレート数: $template_count"
echo "   総プリセット数: $preset_total"
echo "   実行パターン数: $total_count"
echo

echo "📝 実行開始..."
echo "=================================================================="

index=0
success_count=0

# 各テンプレート・プリセットを実行
for item in "${template_preset_list[@]}"; do
    # スペースで分割
    template=$(echo "$item" | cut -d' ' -f1)
    preset=$(echo "$item" | cut -d' ' -f2)
    
    ((index++))
    echo "🔥 [$index/$total_count] $template - $preset プリセット"
    
    filename="demo_${template}_${preset}"
    html_output="$OUTPUT_DIR/html/${filename}.html"
    ass_output="$OUTPUT_DIR/ass/${filename}.ass"
    
    # scroll-cast生成スクリプトを実行
    EXEC_TIME=$(measure_time ./test/generate_scrollcast_with_config.sh "$template" "$preset" "$INPUT_FILE" "$filename")
    execution_status=$?
    
    if [ $execution_status -eq 0 ]; then
        # 生成されたファイルをデモディレクトリに移動
        copy_success=true
        
        if [ -f "contents/html/${filename}.html" ]; then
            cp "contents/html/${filename}.html" "$html_output"
        else
            echo "   ⚠️  HTMLファイルが見つかりません"
            copy_success=false
        fi
        
        if [ -f "contents/ass/${filename}.ass" ]; then
            cp "contents/ass/${filename}.ass" "$ass_output"
        else
            echo "   ⚠️  ASSファイルが見つかりません"
            copy_success=false
        fi
        
        # 共有アセットファイルをコピー（外部JavaScript参照システム用）
        if [ -d "contents/html/shared" ]; then
            mkdir -p "$OUTPUT_DIR/html/shared"
            cp -r "contents/html/shared/"* "$OUTPUT_DIR/html/shared/" 2>/dev/null || true
        fi
        
        if [ -d "contents/html/assets" ]; then
            mkdir -p "$OUTPUT_DIR/html/assets"
            cp -r "contents/html/assets/"* "$OUTPUT_DIR/html/assets/" 2>/dev/null || true
        fi
        
        if [ -d "contents/html/templates" ]; then
            mkdir -p "$OUTPUT_DIR/html/templates"
            cp -r "contents/html/templates/"* "$OUTPUT_DIR/html/templates/" 2>/dev/null || true
        fi
        
        if [ "$copy_success" = true ]; then
            RESULTS[$index]="✅ 成功"
            DURATIONS[$index]="${EXEC_TIME}秒"
            FILENAMES[$index]="$filename"
            echo "   ✅ 生成完了: $html_output"
            ((success_count++))
        else
            RESULTS[$index]="❌ 失敗(コピー)"
            DURATIONS[$index]="${EXEC_TIME}秒"
            FILENAMES[$index]="$filename"
            echo "   ❌ ファイルコピー失敗"
        fi
    else
        RESULTS[$index]="❌ 失敗"
        DURATIONS[$index]="${EXEC_TIME}秒"
        FILENAMES[$index]="$filename"
        echo "   ❌ 生成失敗 (詳細: /tmp/template_output.log)"
    fi
    
    # 進捗表示
    if [ $((index % 5)) -eq 0 ]; then
        echo "   📊 進捗: $index/$total_count 完了 ($success_count 成功)"
    fi
    echo
done

echo "=================================================================="
echo "🎯 動的全テンプレート実行完了!"

# 実行結果サマリー
echo
echo "📊 実行結果サマリー:"
echo "┌─────────────────────────────────────┬──────────┬──────────┐"
echo "│ テンプレート_プリセット             │ 結果     │ 実行時間 │"
echo "├─────────────────────────────────────┼──────────┼──────────┤"

for i in $(seq 1 $index); do
    if [ -n "${FILENAMES[$i]}" ]; then
        printf "│ %-35s │ %-8s │ %-8s │\n" "${FILENAMES[$i]}" "${RESULTS[$i]}" "${DURATIONS[$i]}"
    fi
done

echo "└─────────────────────────────────────┴──────────┴──────────┘"

# 生成されたファイル一覧
echo
echo "📁 生成されたファイル:"
if [ -d "$OUTPUT_DIR/html" ]; then
    html_count=$(find "$OUTPUT_DIR/html" -name "demo_*.html" | wc -l)
    ass_count=$(find "$OUTPUT_DIR/ass" -name "demo_*.ass" | wc -l)
    
    echo "   🌐 HTML ディレクトリ: $OUTPUT_DIR/html/ ($html_count ファイル)"
    for file in "$OUTPUT_DIR/html"/demo_*.html; do
        if [ -f "$file" ]; then
            size=$(ls -lh "$file" | awk '{print $5}')
            basename_file=$(basename "$file")
            echo "      $basename_file ($size)"
        fi
    done
    
    echo "   📝 ASS ディレクトリ: $OUTPUT_DIR/ass/ ($ass_count ファイル)"
    for file in "$OUTPUT_DIR/ass"/demo_*.ass; do
        if [ -f "$file" ]; then
            lines=$(grep -c "Dialogue:" "$file" 2>/dev/null || echo "0")
            basename_file=$(basename "$file")
            echo "      $basename_file (${lines} dialogues)"
        fi
    done
else
    echo "   ⚠️  出力ディレクトリが見つかりません"
fi

echo
echo "📈 統計情報:"
echo "   ✅ 成功: $success_count/$total_count"
echo "   ❌ 失敗: $((total_count - success_count))/$total_count"
echo "   🎯 成功率: $(( (success_count * 100) / total_count ))%"

if [ $success_count -eq $total_count ]; then
    echo
    echo "🎉 全テンプレート・プリセット ($success_count/$total_count) が正常に生成されました！"
    echo
    echo "💡 Next steps:"
    echo "   - ブラウザで $OUTPUT_DIR/html/ のHTMLファイルを開いてテスト"
    echo "   - 新しいテンプレート・プリセットを追加した場合、このスクリプトで自動検出"
    echo "   - 気に入ったプリセットを本番で使用"
    echo
    echo "🔧 個別実行例:"
    echo "   ./test/generate_scrollcast_with_config.sh [template] [preset]"
    exit 0
else
    echo
    echo "⚠️  一部のテンプレート・プリセットで問題が発生しました ($success_count/$total_count 成功)"
    echo "   - 失敗の詳細は /tmp/template_output.log を確認"
    echo "   - 個別実行でデバッグ: ./test/generate_scrollcast_with_config.sh [template] [preset]"
    exit 1
fi