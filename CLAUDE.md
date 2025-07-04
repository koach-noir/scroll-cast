# Claude Code Collaboration Guide - scroll-cast

> **🎯 scroll-cast専用協働フレームワーク**  
> このドキュメントはscroll-castプロジェクトにおけるClaude Codeとの効果的な協働パターンを定義します。

## 🚀 Project Overview

scroll-castは純粋なテキストアニメーション生成システムとして設計された、TextStreamプロジェクトのコアコンポーネントです。

### 核心目標
- **専門特化**: テキストアニメーション生成に特化した高性能システム
- **独立運用**: emotional-decorationシステムとの分離独立
- **CSS Override対応**: 装飾システムとの自然な統合を可能にする設計

### アーキテクチャ原則
```
Text Input → Boxing → Coloring → Packing → Rendering → HTML Output
```
- **Boxing**: テキスト処理とアニメーション用フォーマット
- **Coloring**: アニメーションタイミングとエフェクト生成
- **Packing**: ASS字幕生成
- **Rendering**: HTML/CSS/JS変換
- **Orchestrator**: アニメーションワークフロー調整

## 📋 Development Context

### 重要な制約事項
1. **CSS命名規則の厳格遵守**
   - `.typewriter-container`, `.typewriter-sentence`, `.typewriter-char`
   - `.railway-container`, `.railway-line`
   - `.scroll-container`, `.scroll-line`
   - ADR-013 Dual Repository Architecture仕様に準拠

2. **Decoration System統合要件**
   - CSS Override Architectureサポート必須
   - 基本機能CSS（opacity, transition, display）は変更禁止
   - 視覚的装飾CSS（background, filter, color）は装飾システム担当

3. **パフォーマンス要件**
   - 209,444 characters/second処理能力維持
   - モバイル対応レスポンシブ設計
   - メモリ効率的なアニメーション実装

4. **品質基準**
   - 91.5/100品質スコア維持
   - 包括的テストカバレッジ
   - Type-safe Pydantic validation

### 技術スタック
- **言語**: Python 3.8+
- **フレームワーク**: Pydantic, Jinja2, Click
- **出力**: HTML5, CSS3, JavaScript ES6+, ASS字幕
- **テスト**: pytest, モックHTML生成システム

## ⚙️ Development Workflows

### 新機能開発フロー
```markdown
## 機能追加チェックリスト
- [ ] ADR-012/013の外部装飾システム要件確認
- [ ] CSS命名規則への適合性検証
- [ ] 既存テンプレート（typewriter, railway, scroll）との整合性
- [ ] パフォーマンス影響評価
- [ ] テストケース追加・既存テスト実行
- [ ] ドキュメント更新
```

### テスト実行フロー
```bash
# 全テンプレートのHTML生成テスト
./test/test_html_generation.sh --report

# 特定テンプレートのテスト
./test/test_html_generation.sh --template typewriter

# 個別生成テスト
./test/generate_scrollcast.sh typewriter default test/sample_eng.txt output_name
```

### デバッグパターン
```markdown
## 系統的デバッグアプローチ

### HTML生成問題
1. テンプレートファイル存在確認 (`templates/[template]/[sub-template]/`)
2. CSS命名規則適合性チェック
3. JavaScript初期化関数確認
4. モックHTML生成での動作検証

### CSS Override問題
1. 基本機能CSS（functional CSS）の保持確認
2. 装飾用CSS Custom Propertiesの適切な配置
3. CSS特異性ルールの遵守検証
4. emotional-decorationとの統合テスト

### パフォーマンス問題
1. アニメーション要素数の最適化
2. CSS `will-change` プロパティの適切な使用
3. JavaScript処理の最適化
4. メモリリーク検出
```

## 🔧 Claude Code Optimization

### 効果的なプロンプトパターン

#### 機能開発用プロンプト
```
scroll-castプロジェクトで[機能名]を実装してください。

前提条件:
- ADR-013 Dual Repository Architecture準拠
- CSS Override Architecture対応必須
- 既存テンプレート（typewriter/railway/scroll）との整合性保持
- パフォーマンス要件: 209,444 chars/sec維持

実装要件:
- CSS命名規則厳格遵守
- emotional-decorationとの分離独立
- 包括的テストケース追加
```

#### デバッグ用プロンプト
```
scroll-castで以下の問題を調査・修正してください:

症状: [具体的な症状]
再現手順: [テストコマンド/操作手順]
期待動作: [期待される結果]

調査観点:
- CSS命名規則の適合性
- テンプレートファイル構造
- アニメーション初期化処理
- emotional-decorationとの統合互換性
```

### プロジェクト固有のコンテキスト管理

#### セッション開始時の確認事項
```markdown
## scroll-cast Context Bootstrap

1. **アーキテクチャ理解**
   - docs/adr/ADR-012-external-decoration-injection-system.md
   - docs/adr/ADR-013-dual-repository-architecture.md
   - docs/CSS_NAMING_STANDARDS.md

2. **現在の実装状況**
   - 3つのテンプレート（typewriter, railway, scroll）
   - HTML生成テストシステム完備
   - モックHTML生成機能

3. **制約事項再確認**
   - CSS Override Architecture要件
   - emotional-decorationとの分離独立
   - パフォーマンス・品質基準
```

#### 進捗管理パターン
```markdown
## タスク管理フレームワーク

### 高優先度タスク
- [ ] 核心機能（HTML/ASS生成）の維持・改善
- [ ] CSS命名規則の厳格遵守
- [ ] テストシステムの安定稼働

### 中優先度タスク  
- [ ] 新テンプレート追加
- [ ] パフォーマンス最適化
- [ ] ドキュメント改善

### 低優先度タスク
- [ ] 開発者体験改善
- [ ] ツール最適化
```

## 📚 Reference Integration

### 重要ドキュメント
- **README.md**: プロジェクト概要とクイックスタート
- **docs/CSS_NAMING_STANDARDS.md**: CSS命名規則詳細
- **docs/adr/**: アーキテクチャ決定記録
- **test/**: テストシステムと実行例

### 関連プロジェクト
- **emotional-decoration**: 視覚装飾システム（分離独立）
- **TextStream**: 親プロジェクト（統合アーキテクチャ）

### 外部参照
- CSS Override Architecture ベストプラクティス
- モバイル対応アニメーション設計
- ASS字幕フォーマット仕様

## 🎯 Quality Gates

### コード品質基準
```markdown
## 必須チェック項目

### CSS命名規則
- [ ] テンプレート名-要素名の命名パターン遵守
- [ ] 装飾システム用フック（.decoration-enhanced等）の適切な配置
- [ ] 基本機能CSSと装飾CSSの明確な分離

### パフォーマンス基準
- [ ] アニメーション処理速度: 209,444 chars/sec以上
- [ ] メモリ使用量: 基準値以内
- [ ] モバイル端末での動作確認

### 統合互換性
- [ ] emotional-decorationとのCSS Override動作確認
- [ ] 既存テンプレートとの整合性保持
- [ ] HTMLバリデーション通過
```

### テスト基準
```markdown
## テスト必須項目

### 機能テスト
- [ ] 全テンプレートのHTML生成成功
- [ ] ASS字幕生成成功
- [ ] モックHTML生成機能正常動作

### 統合テスト
- [ ] CSS Override機構の動作確認
- [ ] emotional-decorationとの組み合わせテスト
- [ ] ブラウザでのアニメーション表示確認

### 回帰テスト
- [ ] 既存機能の動作維持確認
- [ ] パフォーマンス回帰なし
- [ ] CSS命名規則違反なし
```

## 🔄 Continuous Integration

### 開発サイクル
```bash
# 1. 開発前確認
./test/test_html_generation.sh --report

# 2. 実装

# 3. テスト実行
./test/test_html_generation.sh --template [template_name]

# 4. 統合確認（emotional-decorationとの組み合わせ）
# (将来的にCSSオーバーライドテストを実装予定)

# 5. ドキュメント更新
```

### 品質保証プロセス
1. **コード変更時**: 必ずテスト実行
2. **CSS変更時**: 命名規則チェック必須
3. **新機能追加時**: ADR更新検討
4. **パフォーマンス影響**: ベンチマーク実行

---

このCLAUDE.mdに記載された協働パターンにより、scroll-castプロジェクトにおける効率的で一貫性のある開発が実現されます。Claude Codeとの協働により、高品質なテキストアニメーション生成システムの継続的改善を進めていきます。