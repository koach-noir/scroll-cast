# テンプレート開発トラブルシューティング

このドキュメントでは、scroll-castでの新規テンプレート開発時によくある問題と解決法をまとめています。

## 🔧 よくある問題と解決法

### 1. 統合テストで「Unknown template」エラー

**症状**:
```bash
./integration_test.sh
❌ FAIL: Unknown template: your_template
```

**原因**: `test/orchestrator_demo.sh`のcase文が未更新

**解決方法**:
```bash
# orchestrator_demo.shを編集
vim test/orchestrator_demo.sh

# 以下のcase文を *)の前に追加:
"your_template")
    TEMPLATE_NAME="your_template"
    ;;
```

**予防策**: `TEMPLATE_DEVELOPMENT_INSTRUCTIONS.md`のStep 5を必ず実行する

---

### 2. 「Timing data extraction not implemented」エラー

**症状**:
```bash
❌ HTML生成エラー: Timing data extraction for your_template not implemented
```

**原因**: `hierarchical_template_converter.py`の`_extract_timing_data`メソッド未更新

**解決方法**:
```python
# src/scrollcast/conversion/hierarchical_template_converter.py に追加

def _extract_timing_data(self) -> List[Dict[str, Any]]:
    """タイミングデータを抽出"""
    if self.template_name == "typewriter_fade":
        return self._extract_typewriter_timing_data()
    elif self.template_name == "your_template":  # 👈 追加
        return self._extract_your_template_timing_data()  # 👈 追加
    # ... 他のテンプレート

# 対応するメソッドも実装
def _extract_your_template_timing_data(self) -> List[Dict[str, Any]]:
    """YourTemplate用タイミングデータを抽出"""
    timing_data = []
    
    for timing in self.data_converter.timings:
        timing_data.append({
            "sequence_index": timing.line_index,
            "start_time": timing.start_time_ms,
            "end_time": timing.end_time_ms,
            "duration": timing.duration_ms,
            "text": timing.text
        })
    
    return timing_data
```

---

### 3. 文字列リテラルエラー（EOL while scanning string literal）

**症状**:
```bash
SyntaxError: EOL while scanning string literal (your_template.py, line 78)
```

**原因**: 自動生成されたコードの改行文字エスケープ問題

**解決方法**:
```python
# ❌ 間違い
return "
".join(dialogue_lines)

# ✅ 正しい
return "\n".join(dialogue_lines)
```

**予防策**: template_generator.pyの出力を確認し、適切なエスケープを使用

---

### 4. テンプレートエンジンに登録されない

**症状**:
```bash
usage: subtitle-generator [-h] [--version] [--list-templates] TEMPLATE ...
subtitle-generator: error: argument TEMPLATE: invalid choice: 'your_template' (choose from ...)
```

**原因**: `template_engine.py`の登録処理でSyntaxError

**解決方法**:
```python
# src/scrollcast/orchestrator/template_engine.py を確認

# try-except文が正しく閉じられているか確認
try:
    from ..coloring.your_template import YourTemplateTemplate
    self.register_template(YourTemplateTemplate())
except ImportError as e:
    print(f"Warning: Failed to import YourTemplateTemplate: {e}")
```

---

### 5. プラグインコンバーターが見つからない

**症状**:
```bash
ModuleNotFoundError: No module named 'scrollcast.conversion.your_template_plugin_converter'
```

**原因**: `hierarchical_template_converter.py`のimport文またはmapping未更新

**解決方法**:
```python
# src/scrollcast/conversion/hierarchical_template_converter.py に追加

# Import文
from .your_template_plugin_converter import YourTemplatePluginConverter

# template_mapping に追加
"your_template": {
    "category": "your_category",
    "converter_class": YourTemplatePluginConverter,
    "template_path": os.path.join(os.path.dirname(__file__), "..", "..", "web", "templates", "your_category", "your_template")
},
```

---

## 🛠️ デバッグのベストプラクティス

### 段階的テスト手順

1. **基本テンプレート生成**:
   ```bash
   python3 tools/template_generator.py your_template category
   ```

2. **構文チェック**:
   ```bash
   python3 -m py_compile src/scrollcast/coloring/your_template.py
   ```

3. **テンプレート登録確認**:
   ```bash
   PYTHONPATH=src python3 -m scrollcast.orchestrator.cli.main --list-templates | grep your_template
   ```

4. **単体テスト**:
   ```bash
   PYTHONPATH=src python3 -m scrollcast.orchestrator.cli.main your_template "Test" --output test.html
   ```

5. **統合テスト**:
   ```bash
   ./test/demo_all_config.sh
   ```

6. **フル統合テスト**:
   ```bash
   ./integration_test.sh
   ```

### ログ確認方法

統合テストで失敗した場合：
```bash
# 詳細ログを確認
cat /tmp/demo_all_config.log

# 個別実行でデバッグ
PYTHONPATH=src python3 -m scrollcast.orchestrator.cli.main your_template "Debug text" --preset default
```

---

## 📋 チェックリスト

新規テンプレート作成時の必須確認項目：

- [ ] `template_generator.py`実行成功
- [ ] `template_engine.py`への登録（syntax errorなし）
- [ ] `hierarchical_template_converter.py`への追加（import + mapping + timing method）
- [ ] `orchestrator_demo.sh`のcase文追加
- [ ] 単体テスト成功
- [ ] 統合テスト成功（`./test/demo_all_config.sh`）
- [ ] フル統合テスト成功（`./integration_test.sh`）

---

## 🆘 緊急時の対処

### 既存テンプレートが動かなくなった場合

```bash
# 変更をリセット
git checkout HEAD -- src/scrollcast/orchestrator/template_engine.py
git checkout HEAD -- src/scrollcast/conversion/hierarchical_template_converter.py

# 正常な状態から再開
./test/demo_all_config.sh
```

### template_generator.pyが生成したファイルに問題がある場合

```bash
# 生成されたファイルを削除
rm -f src/scrollcast/coloring/your_template.py
rm -f src/scrollcast/conversion/your_template_plugin_converter.py
rm -f src/web/templates/category/your_template/sc-template.css
rm -f src/web/plugins/your-template-display-plugin.js
rm -f config/your_template.yaml

# template_engine.pyとhierarchical_template_converter.pyから該当行を手動削除
# 再度 template_generator.py を実行
```

---

このトラブルシューティングガイドにより、テンプレート開発中の問題を迅速に解決できます。