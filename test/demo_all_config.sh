#!/bin/bash

# Demo All Config Script for scroll-cast
# 全テンプレート・プリセット一括実行スクリプト（新web構造対応）
# Usage: ./test/demo_all_config.sh [input_file]

# デフォルト値
INPUT_FILE=${1:-"test/sample_eng.txt"}
BASE_OUTPUT_DIR=${2:-"output-default"}
OUTPUT_DIR="$BASE_OUTPUT_DIR/web"
ASS_OUTPUT_DIR="$BASE_OUTPUT_DIR/ass"
CONFIG_DIR="config"

# ヘルプ表示
if [ "$1" = "-h" ] || [ "$1" = "--help" ]; then
    echo "🎬 Demo All Config Script for scroll-cast"
    echo
    echo "全テンプレート・プリセットを一括実行（新web構造対応）"
    echo
    echo "Usage: $0 [input_file] [output_dir]"
    echo
    echo "Arguments:"
    echo "  input_file   Input text file (default: test/sample_eng.txt)"
    echo "  output_dir   Base output directory (default: output-default)"
    echo
    echo "動的検出機能:"
    echo "  - $CONFIG_DIR/ から *.yaml ファイルを自動検出"
    echo "  - 各YAMLファイルから presets を自動抽出"
    echo "  - テンプレート・プリセット追加時の手動更新不要"
    echo
    echo "Output:"
    echo "  📁 Web Directory: [output_dir]/web/"
    echo "  🌐 HTML files: demo_[template]_[preset].html"
    echo "  📝 ASS files:  [output_dir]/ass/demo_[template]_[preset].ass"
    echo
    exit 0
fi

# 入力ファイルの存在確認
if [ ! -f "$INPUT_FILE" ]; then
    echo "❌ Error: Input file '$INPUT_FILE' not found"
    exit 1
fi

# 設定ディレクトリの存在確認
if [ ! -d "$CONFIG_DIR" ]; then
    echo "❌ Error: Configuration directory '$CONFIG_DIR' not found"
    exit 1
fi

# 出力フォルダの作成
mkdir -p "$OUTPUT_DIR" "$ASS_OUTPUT_DIR"

echo "🎬 Demo All Config - 全テンプレート・プリセット一括実行"
echo "   Input: $INPUT_FILE"
echo "   Config Directory: $CONFIG_DIR/"
echo "   Web Output: $OUTPUT_DIR/"
echo "   ASS Output: $ASS_OUTPUT_DIR/"
echo

# 実行結果を記録する配列
declare -a RESULTS
declare -a DURATIONS
declare -a FILENAMES

# 実行時間計測関数
measure_time() {
    local start_time=$(date +%s)
    "$@" > /tmp/demo_all_config.log 2>&1
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
            # テンプレートが利用可能かチェック
            available_templates=$(PYTHONPATH=src python3 -m scrollcast.orchestrator.cli.main --list-templates 2>/dev/null | grep "^  $template_name" | wc -l)
            if [ "$available_templates" -eq 0 ]; then
                echo "   ⚠️  $template_name: テンプレートが利用できません（スキップ）"
                continue
            fi
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
    html_output="$OUTPUT_DIR/${filename}.html"
    ass_output="$ASS_OUTPUT_DIR/${filename}.ass"
    
    # orchestrator_demo.shを実行（出力先指定）
    EXEC_TIME=$(measure_time ./test/orchestrator_demo.sh "$template" "$preset" "$INPUT_FILE" "$filename" "$BASE_OUTPUT_DIR")
    execution_status=$?
    
    if [ $execution_status -eq 0 ]; then
        # orchestrator_demo.shが指定された出力先に直接出力
        files_success=true
        
        if [ -f "$html_output" ]; then
            echo "   ✅ HTML: $(basename "$html_output")"
        else
            echo "   ⚠️  HTMLファイルが見つかりません: $html_output"
            files_success=false
        fi
        
        if [ -f "$ass_output" ]; then
            echo "   ✅ ASS: $(basename "$ass_output")"
        else
            echo "   ⚠️  ASSファイルが見つかりません: $ass_output"
            files_success=false
        fi
        
        if [ "$files_success" = true ]; then
            RESULTS[$index]="✅ 成功"
            DURATIONS[$index]="${EXEC_TIME}秒"
            FILENAMES[$index]="$filename"
            ((success_count++))
        else
            RESULTS[$index]="❌ 失敗(ファイル)"
            DURATIONS[$index]="${EXEC_TIME}秒"
            FILENAMES[$index]="$filename"
        fi
    else
        RESULTS[$index]="❌ 失敗"
        DURATIONS[$index]="${EXEC_TIME}秒"
        FILENAMES[$index]="$filename"
        echo "   ❌ 生成失敗 (詳細: /tmp/demo_all_config.log)"
    fi
    
    # 進捗表示
    if [ $((index % 5)) -eq 0 ]; then
        echo "   📊 進捗: $index/$total_count 完了 ($success_count 成功)"
    fi
    echo
done

echo "=================================================================="
echo "🎯 全テンプレート・プリセット実行完了!"

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

if [ -d "$OUTPUT_DIR" ]; then
    html_count=$(find "$OUTPUT_DIR" -name "demo_*.html" | wc -l)
    
    echo "   🌐 Web ディレクトリ: $OUTPUT_DIR/ ($html_count ファイル)"
    for file in "$OUTPUT_DIR"/demo_*.html; do
        if [ -f "$file" ]; then
            size=$(ls -lh "$file" | awk '{print $5}')
            basename_file=$(basename "$file")
            echo "      $basename_file ($size)"
        fi
    done
fi

if [ -d "$ASS_OUTPUT_DIR" ]; then
    ass_count=$(find "$ASS_OUTPUT_DIR" -name "demo_*.ass" | wc -l)
    
    echo "   📝 ASS ディレクトリ: $ASS_OUTPUT_DIR/ ($ass_count ファイル)"
    for file in "$ASS_OUTPUT_DIR"/demo_*.ass; do
        if [ -f "$file" ]; then
            lines=$(grep -c "Dialogue:" "$file" 2>/dev/null || echo "0")
            basename_file=$(basename "$file")
            echo "      $basename_file (${lines} dialogues)"
        fi
    done
fi

# アセットファイル情報
if [ -f "$OUTPUT_DIR/asset-manifest.json" ]; then
    asset_count=$(grep -o '"deployed_assets"' "$OUTPUT_DIR/asset-manifest.json" | wc -l)
    if [ $asset_count -gt 0 ]; then
        echo "   📦 アセット: lib/, plugins/, templates/ (マニフェスト確認)"
    fi
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
    echo "   - ブラウザで $OUTPUT_DIR/ のHTMLファイルを開いてテスト"
    echo "   - 新しいテンプレート・プリセットを追加した場合、このスクリプトで自動検出"
    echo "   - src/web/ 構造での静的アセット配信を確認"
    echo
    echo "🔧 個別実行例:"
    echo "   PYTHONPATH=src python3 -m scrollcast.orchestrator.cli.main [template] \"text\" --preset [preset]"
    exit 0
else
    echo
    echo "⚠️  一部のテンプレート・プリセットで問題が発生しました ($success_count/$total_count 成功)"
    echo "   - 失敗の詳細は /tmp/demo_all_config.log を確認"
    echo "   - 個別実行でデバッグ: PYTHONPATH=src python3 -m scrollcast.orchestrator.cli.main [template] \"text\" --preset [preset]"
    exit 1
fi