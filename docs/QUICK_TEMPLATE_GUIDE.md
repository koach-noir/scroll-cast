# Quick Template Addition Guide

## 🚀 新テンプレート追加の20行手順

### 1. 準備 (2分)
```bash
# テンプレート名を決定 (例: my_template)
export TEMPLATE_NAME="my_template"
export CATEGORY="scroll"  # typewriter, railway, scroll から選択
```

### 2. テンプレート自動生成ツールの使用 (1分)
```bash
cd scroll-cast
python tools/template_generator.py $TEMPLATE_NAME $CATEGORY
```

### 3. ASS生成モジュールの実装 (10分)
```python
# src/scrollcast/coloring/{template_name}.py
# 自動生成されたファイルの以下のメソッドを実装:
# - generate_ass_from_formatted() - ASS効果を生成
# - calculate_total_duration() - 総時間計算
```

### 4. JavaScript プラグインの実装 (5分)
```javascript
// 生成されたファイルの animateTemplateLine() メソッドを実装
// アニメーション仕様を具体化
```

### 5. CSSテンプレートの実装 (3分)
```css
/* アニメーション固有のスタイルを追加 */
/* 自動生成されたファイルをカスタマイズ */
```

### 6. 設定ファイルの調整 (1分)
```yaml
# config/{template_name}.yaml
# default_parameters を調整
```

### 7. テスト実行 (2分)
```bash
# 個別テスト
PYTHONPATH=src python3 -m scrollcast.orchestrator.cli.main $TEMPLATE_NAME "Test" --output test.html

# 統合テスト
./test/demo_all_config.sh
```

### 8. ブラウザ確認 (1分)
```bash
open contents/html/demo_${TEMPLATE_NAME}_default.html
```

## ⚠️ 重要な制約事項

1. **既存ファイルの変更禁止**: 既存テンプレートファイルは一切変更しない
2. **CSS命名規則**: `.text-container[data-template="X"]` + `.text-line` パターン厳守
3. **プラグインベース**: BaseTemplate, PluginConverterBase継承必須
4. **外部アセット**: JavaScript/CSS外部参照アーキテクチャ遵守

## 🔧 自動生成ツールが生成するファイル

- `src/scrollcast/coloring/{template_name}.py` - ASS生成モジュール
- `src/scrollcast/conversion/{template_name}_plugin_converter.py` - プラグインコンバーター
- `src/web/templates/{category}/{template_name}/sc-template.css` - CSS
- `config/{template_name}.yaml` - 設定ファイル
- `contents/web/plugins/{template_name}-display-plugin.js` - JavaScript プラグイン
- 統合登録の更新 (template_engine.py)

## 📋 実装チェックリスト

- [ ] ASS生成モジュール実装完了
- [ ] JavaScript プラグイン実装完了
- [ ] CSS アニメーション実装完了
- [ ] 設定ファイル調整完了
- [ ] 個別テスト成功
- [ ] 統合テスト成功
- [ ] ブラウザ動作確認完了

## 💡 開発のコツ

- **段階的実装**: 各コンポーネントを個別にテストしながら進める
- **既存参照**: 類似テンプレートのコードを参考にする
- **データ互換性**: JavaScript で異なるデータ構造に対応する

**所要時間**: 約25分（慣れれば15分）