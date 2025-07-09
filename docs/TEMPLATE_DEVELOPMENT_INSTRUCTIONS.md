# テンプレート開発作業指示書

## 📋 概要

このドキュメントは、scroll-castプロジェクトで新しいアニメーションテンプレートを開発する際の作業指示書です。自動生成ツールを使用することで、約25分で新しいテンプレートを作成できます。

## 🚀 作業手順

### Step 1: 事前準備 (1分)
```bash
# 作業ディレクトリに移動
cd scroll-cast

# 最新の状態に更新
git pull origin main

# テンプレート名とカテゴリを決定
# テンプレート名: snake_case形式 (例: wave_effect, pulse_animation, fade_in_out)
# カテゴリ: typewriter, railway, scroll のいずれか
```

### Step 2: 自動生成 (1分)
```bash
# テンプレート骨格を自動生成
python3 tools/template_generator.py [template_name] [category]

# 実行例:
python3 tools/template_generator.py wave_effect scroll
```

### Step 3: 実装 (15-20分)

#### 3.1 ASS効果実装 (最重要・10分)
ファイル: `src/scrollcast/coloring/[template_name].py`

```python
def _generate_ass_effect(self, text: str, font_size: int, start_time: float, duration: float) -> str:
    """ASS効果を生成（テンプレート固有実装が必要）"""
    duration_ms = int(duration * 1000)
    
    # TODO: ここにテンプレート固有のASS効果を実装
    # 例: 下から上へのスクロール
    return (
        f"{{\\pos(960,1200)\\fs{font_size}\\an5\\c&HFFFFFF&"
        f"\\move(960,1200,960,-120,0,{duration_ms})}}"
        f"{text}"
    )
```

**ASS効果の実装例:**
- **フェード**: `\\fad(500,500)` - 0.5秒でフェードイン/アウト
- **移動**: `\\move(x1,y1,x2,y2,t1,t2)` - 座標移動
- **回転**: `\\frz[angle]` - Z軸回転
- **スケール**: `\\fscx[scale]\\fscy[scale]` - 拡大縮小
- **色変更**: `\\c&H[color]&` - テキスト色

#### 3.2 JavaScript アニメーション実装 (5分)
ファイル: `src/web/plugins/[template-name]-display-plugin.js`

```javascript
animateTemplateLine: function(line, sequenceData) {
    const duration = sequenceData.duration || sequenceData.total_duration || 8000;
    const durationMs = duration > 100 ? duration : duration * 1000;
    
    // 初期状態を設定
    line.style.display = 'block';
    line.style.opacity = '1';
    line.style.transform = 'translate(-50%, -50%)';
    
    // TODO: テンプレート固有のアニメーション効果を実装
    // 例: 下から上へのスクロール
    line.style.transform = 'translate(-50%, -50%) translateY(100vh)';
    
    setTimeout(() => {
        const transitionDuration = durationMs / 1000;
        line.style.transition = `transform ${transitionDuration}s linear`;
        line.style.transform = 'translate(-50%, -50%) translateY(-100vh)';
        
        // アニメーション完了後のクリーンアップ
        setTimeout(() => {
            line.style.display = 'none';
            line.style.transition = '';
            line.style.transform = '';
        }, durationMs);
    }, 50);
}
```

#### 3.3 CSS スタイル調整 (5分)
ファイル: `src/web/templates/[category]/[template_name]/sc-template.css`

```css
/* TODO: テンプレート固有のアニメーション効果を実装 */
.text-container[data-template="[category}"] .text-line.animating {
    display: block;
    opacity: 1;
    /* カスタムアニメーション効果をここに追加 */
}
```

### Step 4: テスト・検証 (3分)
```bash
# 動作テスト
PYTHONPATH=src python3 -m scrollcast.orchestrator.cli.main [template_name] "Hello World Test" --output test.html

# ブラウザ確認
open test.html

# 統合テスト（全テンプレートの動作確認）
./test/demo_all_config.sh
```

### Step 5: 完了・納品 (1分)
```bash
# テストファイルのクリーンアップ
rm -f test.html test.ass

# コミット・プッシュ
git add .
git commit -m "Add [template_name] template

- Implement [具体的な効果の説明]
- Support [カテゴリ] category animations
- Include responsive design and CSS override hooks

🤖 Generated with [Claude Code](https://claude.ai/code)

Co-Authored-By: Claude <noreply@anthropic.com>"

git push origin main
```

## ⚠️ 重要な制約事項

### 絶対に守るべきルール
1. **既存ファイルの変更禁止** - 既存テンプレートファイルは一切変更しない
2. **CSS命名規則厳守** - `.text-container[data-template="X"]` + `.text-line` パターン
3. **アーキテクチャ遵守** - 外部アセット参照、CSS Override対応

### 実装のコツ
- **段階的テスト** - 各段階で動作確認しながら進める
- **既存参照** - 類似テンプレート（revolver_up, railway_scroll等）のコードを参考にする
- **データ互換性** - JavaScript で `sequenceData.duration || sequenceData.total_duration || 8000` のような互換性対応

## 📊 期待される成果
- **所要時間**: 約25分（慣れれば15分）
- **品質**: 自動生成により構文エラーゼロ、アーキテクチャ準拠
- **統合性**: 自動的に全システムに統合済み

## 🆘 トラブルシューティング

### よくある問題と解決法

#### 1. 構文エラーが発生した場合
```bash
# Python構文チェック
python3 -m py_compile src/scrollcast/coloring/[template_name].py
```

#### 2. アニメーションが動作しない場合
- ブラウザの開発者ツールでJavaScriptエラーを確認
- `sequenceData`の構造を`console.log`で確認

#### 3. 既存ファイルが変更されてしまった場合
```bash
# 変更をリセット
git checkout HEAD -- [変更されたファイル]
```

#### 4. 統合テストが失敗した場合
```bash
# 個別テストで問題箇所を特定
PYTHONPATH=src python3 -m scrollcast.orchestrator.cli.main [template_name] "Test" --output debug.html
```

## 📚 参考資料

- `docs/QUICK_TEMPLATE_GUIDE.md` - 簡潔な追加手順
- `docs/TEMPLATE_ADDITION_GUIDE.md` - 詳細な実装ガイド
- 既存テンプレートコード:
  - `src/scrollcast/coloring/revolver_up.py` - ASS実装例
  - `src/web/plugins/revolver-up-display-plugin.js` - JavaScript実装例
  - `src/web/templates/scroll/revolver_up/sc-template.css` - CSS実装例

---

## 📝 指示例

**管理者からの指示例:**
> このドキュメント `docs/TEMPLATE_DEVELOPMENT_INSTRUCTIONS.md` を読んでテンプレート新規作成をお願いします。新規テンプレートの仕様は「波打つように文字が左右に揺れながら上昇するアニメーション」です。テンプレート名は `wave_rise`、カテゴリは `scroll` でお願いします。

**開発者の作業:**
1. 上記手順に従って `python3 tools/template_generator.py wave_rise scroll` 実行
2. 3つのファイルで波打つ効果を実装
3. テスト・検証後にコミット・プッシュ

このドキュメントにより、具体的で実行可能な指示が可能になります。