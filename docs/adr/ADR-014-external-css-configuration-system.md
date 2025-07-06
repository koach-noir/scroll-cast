# ADR-014: External CSS Configuration System

## Status
**Implemented** - 2025-07-06

## Context

scroll-castのHTML生成システムにおいて、emotional-decorationなど外部システムから提供されるCSSファイルを統合する必要があった。従来は、必要なCSSファイルのリンクがプラグインコンバーター内にハードコードされており、新しいCSSファイルの追加や変更時にソースコード修正が必要であった。

### 課題
- 外部CSSファイルのリンクがハードコード（保守性の問題）
- 新しいemotional-decorationのCSSファイル追加時にソースコード修正が必要
- 将来的な外部システム拡張時の拡張性不足

### 要件
- 設定ファイルベースのCSS管理
- emotional-decorationとの分離原則維持
- 将来の外部システム拡張への対応
- 既存機能への影響なし

## Decision

**外部CSS設定ファイルシステム**を採用し、YAML設定ファイルによる管理を実装する。

### 実装内容

#### 1. 設定ファイル: `config/external_css_includes.yaml`
```yaml
# External CSS Includes Configuration
version: "1.0.0"
description: "Configuration for external CSS files to be included in generated HTML"

emotional_decoration:
  enabled: true
  base_path: "../css/"
  files:
    - name: "text-color-simple.css"
      description: "Template-specific text color enhancement"
      required: true
    - name: "scroll-cast-text-color-enhancement.css" 
      description: "Advanced color and visual effects"
      required: false

future_systems:
  # 将来の外部システム用セクション

settings:
  auto_discovery: false
  include_comments: true
  order_priority: ["emotional_decoration"]
```

#### 2. 実装ファイル: `src/scrollcast/conversion/plugin_converter_base.py`

**新規メソッド:**
- `_load_external_css_config()`: YAML設定読み込み
- `_get_external_css_links()`: 設定ベースのCSSリンク生成

**修正メソッド:**
- `_generate_template_css_links()`: 設定ファイルベースに変更

### アーキテクチャ図
```
HTML Generation Pipeline:
┌─────────────────────────────────────────────────────────────┐
│ Plugin Converter Base                                       │
│ ┌─────────────────────┐  ┌───────────────────────────────┐ │
│ │ Template CSS Links  │  │ External CSS Configuration    │ │
│ │ - sc-template.css   │  │ - external_css_includes.yaml │ │
│ └─────────────────────┘  └───────────────────────────────┘ │
│              │                           │                 │
│              └───────────┬───────────────┘                 │
│                          ▼                                 │
│ ┌─────────────────────────────────────────────────────────┐ │
│ │ _generate_template_css_links()                          │ │
│ │ 1. Template CSS + 2. External CSS                      │ │
│ └─────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────┐
│ Generated HTML Output                                       │
│ <link rel="stylesheet" href="templates/.../sc-template.css">│
│ <link rel="stylesheet" href="../css/text-color-simple.css"> │
│ <link rel="stylesheet" href="../css/enhancement.css">       │
└─────────────────────────────────────────────────────────────┘
```

## Benefits

### 保守性向上
- **設定ファイル管理**: CSSファイルの追加・削除が設定ファイル編集のみで完了
- **コード分離**: HTMLジェネレーターのコードに外部依存を含めない
- **バージョン管理**: 設定ファイルで機能のON/OFF制御可能

### 拡張性確保
- **将来システム対応**: 新しい外部システム用セクションを簡単に追加
- **優先順位制御**: `order_priority`でCSS読み込み順序を制御
- **自動発見機能**: 将来的にディレクトリスキャン機能追加可能

### emotional-decoration統合
- **分離原則維持**: scroll-castコードにemotional-decoration固有の知識を含めない
- **非破壊的統合**: 既存のテンプレート生成に影響なし
- **柔軟な連携**: emotional-decorationの進化に柔軟対応

## Usage Guide

### 開発者向け使用方法

#### 1. 新しいCSSファイルの追加
```yaml
# config/external_css_includes.yaml
emotional_decoration:
  enabled: true
  base_path: "../css/"
  files:
    - name: "text-color-simple.css"
      description: "Template-specific text color enhancement"
      required: true
    - name: "new-enhancement.css"  # ← 新規追加
      description: "New visual enhancement"
      required: false
```

#### 2. 新しい外部システムの追加
```yaml
# 新しいシステム用セクション追加
visual_effects:
  enabled: true
  base_path: "../effects/"
  files:
    - name: "particle-effects.css"
      description: "Particle animation effects"
      required: false

settings:
  order_priority: ["emotional_decoration", "visual_effects"]  # 順序制御
```

#### 3. システムの無効化
```yaml
emotional_decoration:
  enabled: false  # ← システム全体を無効化
```

### 設定ファイル要素説明

| 要素 | 型 | 説明 | 例 |
|------|-----|------|-----|
| `enabled` | boolean | システムの有効/無効 | `true` |
| `base_path` | string | CSSファイルのベースパス | `"../css/"` |
| `files[].name` | string | CSSファイル名 | `"text-color-simple.css"` |
| `files[].description` | string | HTMLコメント用説明 | `"Text color enhancement"` |
| `files[].required` | boolean | 必須ファイルかどうか | `true` |

### エラーハンドリング

設定ファイルが見つからない、または不正な場合：
```
⚠️  外部CSS設定読み込み警告: [Errno 2] No such file or directory: 'config/external_css_includes.yaml'
```

システムは警告を出力して既存のテンプレートCSSのみで継続動作します。

### 生成される HTML

設定に基づいて以下のHTMLが生成されます：
```html
<head>
    <!-- ScrollCast Shared Styles -->
    <link rel="stylesheet" href="shared/scrollcast-styles.css">
    <!-- Template Specific Styles -->
    <link rel="stylesheet" href="templates/typewriter/typewriter_fade/sc-template.css">
    <!-- Template-specific text color enhancement -->
    <link rel="stylesheet" href="../css/text-color-simple.css">
    <!-- Advanced color and visual effects -->
    <link rel="stylesheet" href="../css/scroll-cast-text-color-enhancement.css">
</head>
```

## Migration Guide

### 既存コードからの移行

**Before (ハードコード):**
```python
def _generate_template_css_links(self) -> str:
    css_path = f"templates/{category}/{name}/sc-template.css"
    links = [
        '    <!-- Template Specific Styles -->',
        f'    <link rel="stylesheet" href="{css_path}">',
        '    <!-- Emotional Decoration CSS -->',
        '    <link rel="stylesheet" href="../css/text-color-simple.css">'
    ]
    return '\n'.join(links)
```

**After (設定ファイルベース):**
```python
def _generate_template_css_links(self) -> str:
    css_path = f"templates/{category}/{name}/sc-template.css"
    links = [
        '    <!-- Template Specific Styles -->',
        f'    <link rel="stylesheet" href="{css_path}">'
    ]
    
    # 外部CSS設定から追加のリンクを取得
    external_css_links = self._get_external_css_links()
    if external_css_links:
        links.extend(external_css_links)
    
    return '\n'.join(links)
```

### 下位互換性

- 設定ファイルが存在しない場合、既存動作を維持
- 既存のテンプレートCSS生成に影響なし
- HTMLテンプレート構造は変更なし

## Testing

### テスト方法
```bash
# 単体テンプレート生成テスト
./test/generate_scrollcast_with_config.sh typewriter_fade cinematic ../sample_eng.txt test_external_css

# 生成されたHTMLでCSSリンク確認
grep -A5 -B5 "text-color-simple.css" contents/html/test_external_css.html

# 統合テスト
./integration_test.sh
```

### 期待される結果
- 設定ファイルで指定したCSSファイルが正しくHTMLに含まれる
- コメントが適切に生成される
- 既存機能に影響がない

## Future Considerations

### 将来の拡張可能性

1. **自動CSS発見機能**
   ```yaml
   settings:
     auto_discovery: true  # ディレクトリスキャン有効化
     discovery_patterns: ["*.css", "*.scss"]
   ```

2. **条件付きCSS読み込み**
   ```yaml
   files:
     - name: "mobile-enhancements.css"
       condition: "mobile_device"
   ```

3. **動的パス解決**
   ```yaml
   files:
     - name: "{template_name}-specific.css"  # テンプレート名で動的パス
   ```

## References

- [ADR-012: External Decoration Injection System](ADR-001-external-decoration-injection-system.md)
- [CSS Naming Standards](../CSS_NAMING_STANDARDS.md)
- [emotional-decoration Integration Guide](../../../emotional-decoration/docs/SCROLL-CAST-INTEGRATION.md)

---

**Author**: TextStream Development Team  
**Date**: 2025-07-06  
**Version**: 1.0.0