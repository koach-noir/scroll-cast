#!/usr/bin/env python3
"""
Template Generator Tool
テンプレート自動生成ツール

Usage:
    python template_generator.py <template_name> <category>
    
Example:
    python template_generator.py my_template scroll
"""

import os
import sys
import re
from typing import Dict, List
from pathlib import Path


class TemplateGenerator:
    """テンプレート自動生成クラス"""
    
    def __init__(self, template_name: str, category: str):
        self.template_name = template_name
        self.category = category
        self.class_name = self._to_pascal_case(template_name)
        self.base_path = Path(__file__).parent.parent
        
    def _to_pascal_case(self, snake_str: str) -> str:
        """snake_caseをPascalCaseに変換"""
        components = snake_str.split('_')
        return ''.join(word.capitalize() for word in components)
    
    def generate_all_files(self) -> None:
        """全ファイルを生成"""
        print(f"🚀 Generating template: {self.template_name} (category: {self.category})")
        
        # 1. ASS生成モジュール
        self._generate_ass_coloring_module()
        
        # 2. プラグインコンバーター
        self._generate_plugin_converter()
        
        # 3. CSS テンプレート
        self._generate_css_template()
        
        # 4. JavaScript プラグイン
        self._generate_javascript_plugin()
        
        # 5. 設定ファイル
        self._generate_config_file()
        
        # 6. 統合登録の更新
        self._update_template_engine()
        self._update_hierarchical_converter()
        
        print(f"✅ Template generation completed!")
        print(f"📁 Generated files:")
        print(f"   - src/scrollcast/coloring/{self.template_name}.py")
        print(f"   - src/scrollcast/conversion/{self.template_name}_plugin_converter.py")
        print(f"   - src/web/templates/{self.category}/{self.template_name}/sc-template.css")
        print(f"   - config/{self.template_name}.yaml")
        print(f"   - src/web/plugins/{self.template_name.replace('_', '-')}-display-plugin.js")
        print(f"   - Updated: src/scrollcast/orchestrator/template_engine.py")
    
    def _generate_ass_coloring_module(self) -> None:
        """ASS生成モジュールを生成"""
        content = f'''"""
{self.class_name} Template
{self.template_name} - ASS生成特化版
"""

from typing import List
from .base import BaseTemplate, SubtitleTemplate, TemplateParameter, TimingInfo
from ..boxing import FormattedText
from ..utils.debug_logger import coloring_logger


class {self.class_name}Template(BaseTemplate):
    """{self.template_name}テンプレート（ASS生成特化）"""
    
    def __init__(self):
        super().__init__()
        self.logger = coloring_logger("{self.template_name}")
    
    @property
    def template_info(self) -> SubtitleTemplate:
        return SubtitleTemplate(
            name="{self.template_name}",
            description="{self.template_name}アニメーション効果",
            parameters={{
                "duration": TemplateParameter(
                    name="duration",
                    type=float,
                    default=8.0,
                    description="アニメーション継続時間（秒）",
                    min_value=1.0,
                    max_value=30.0
                ),
                "delay": TemplateParameter(
                    name="delay",
                    type=float,
                    default=0.5,
                    description="行間の遅延時間（秒）",
                    min_value=0.0,
                    max_value=5.0
                ),
                "font_size": TemplateParameter(
                    name="font_size",
                    type=int,
                    default=64,
                    description="フォントサイズ",
                    min_value=24,
                    max_value=120
                )
            }}
        )
    
    def generate_ass_from_formatted(self, formatted_text: FormattedText, **kwargs) -> str:
        """整形済みテキストからASS字幕を生成
        
        Args:
            formatted_text: 整形済みテキスト
            **kwargs: テンプレートパラメータ
        
        Returns:
            完全なASS字幕内容
        """
        self.logger.layer_boundary("from", "boxing", f"{{len(formatted_text.lines)}}行受信")
        
        # パラメータ検証
        params = self.validate_parameters(**kwargs)
        self.logger.processing_step("パラメータ検証", f"duration={{params['duration']}}")
        
        # 解像度取得
        resolution = params.get('resolution', (1080, 1920))
        
        # ASSヘッダー生成
        ass_content = self.generate_ass_header(resolution=resolution, **{{k: v for k, v in params.items() if k != 'resolution'}})
        
        # 各行のDialogue行を生成
        dialogue_lines = self._generate_dialogue_lines(formatted_text, params)
        
        # 完全なASS内容を構築
        ass_content += "\n".join(dialogue_lines)
        
        self.logger.output_data(f"ASS行数: {{len(dialogue_lines)}}", "生成されたASS")
        self.logger.layer_boundary("to", "packing", f"{{len(dialogue_lines)}}行のDialogue")
        
        return ass_content
    
    def calculate_total_duration(self, formatted_text: FormattedText, **kwargs) -> float:
        """総再生時間を計算
        
        Args:
            formatted_text: 整形済みテキスト
            **kwargs: テンプレートパラメータ
        
        Returns:
            総時間（秒）
        """
        params = self.validate_parameters(**kwargs)
        text_lines = formatted_text.get_text_lines()
        
        duration = params['duration']
        delay = params['delay']
        
        # 基本計算: 最後の行の開始時間 + 表示時間
        total_time = len(text_lines) * delay + duration
        
        self.logger.processing_step("時間計算", f"{{len(text_lines)}}行 × {{delay}}s + {{duration}}s = {{total_time}}s")
        
        return total_time
    
    def _generate_dialogue_lines(self, formatted_text: FormattedText, params: dict) -> List[str]:
        """各行のDialogue行を生成"""
        text_lines = formatted_text.get_text_lines()
        dialogue_lines = []
        
        duration = params['duration']
        delay = params['delay']
        font_size = params['font_size']
        
        for i, line in enumerate(text_lines):
            if not line.strip():
                continue
            
            # タイミング計算
            start_time = i * delay
            end_time = start_time + duration
            
            # ASS効果生成（TODO: テンプレート固有の効果を実装）
            ass_effect = self._generate_ass_effect(line, font_size, start_time, duration)
            
            # TimingInfo作成
            timing = TimingInfo(start_time=start_time, end_time=end_time, layer=0)
            
            # Dialogue行作成
            dialogue_line = self.create_dialogue_line(ass_effect, timing)
            dialogue_lines.append(dialogue_line)
        
        return dialogue_lines
    
    def _generate_ass_effect(self, text: str, font_size: int, start_time: float, duration: float) -> str:
        """ASS効果を生成（テンプレート固有実装が必要）"""
        # TODO: テンプレート固有のASS効果を実装
        # 例: 下から上へのスクロール
        duration_ms = int(duration * 1000)
        
        return (
            f"{{{{\\\\pos(960,1200)\\\\fs{{font_size}}\\\\an5\\\\c&HFFFFFF&"
            f"\\\\move(960,1200,960,-120,0,{{duration_ms}}}}}}"
            f"{{text}}"
        )
'''
        
        # ディレクトリ作成とファイル書き込み
        output_path = self.base_path / "src" / "scrollcast" / "coloring" / f"{self.template_name}.py"
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(content, encoding='utf-8')
        
    def _generate_plugin_converter(self) -> None:
        """プラグインコンバーターを生成"""
        content = f'''"""
{self.class_name} Plugin-based ASS to HTML converter
プラグイン型{self.class_name}テンプレート実装
"""

import re
import json
from typing import List, Tuple, NamedTuple
from .utils import ASSTimeUtils, ASSMetadataExtractor, ASSDialogueParser
from .plugin_system import TemplateConfig
from .plugin_converter_base import PluginConverterBase


class {self.class_name}Timing(NamedTuple):
    """タイミング情報"""
    text: str
    start_time_ms: int
    end_time_ms: int
    duration_ms: int
    line_index: int


class {self.class_name}PluginConverter(PluginConverterBase):
    """プラグイン型{self.class_name} ASS→HTML変換クラス"""
    
    def __init__(self):
        super().__init__()
        self.timings: List[{self.class_name}Timing] = []
    
    def get_template_config(self) -> TemplateConfig:
        """{self.class_name}テンプレートのプラグイン設定"""
        return TemplateConfig(
            template_name="{self.template_name}",
            navigation_unit="line",
            required_plugins=["auto_play", "{self.template_name}_display"],
            plugin_configs={{
                "auto_play": {{
                    "auto_start": True,
                    "initial_delay": 500
                }},
                "{self.template_name}_display": {{
                    "element_selector": ".text-line"
                }}
            }}
        )
    
    def parse_ass_file(self, ass_file_path: str) -> None:
        """ASSファイルを解析"""
        content = self.read_ass_file_content(ass_file_path)
        
        # メタデータ抽出
        self.metadata = ASSMetadataExtractor.extract_metadata(content, "{self.class_name}")
        
        # Dialogue行の抽出と総時間計算
        dialogue_matches = ASSDialogueParser.parse_dialogues(content)
        self.total_duration_ms = ASSDialogueParser.calculate_total_duration(dialogue_matches)
        self.metadata.total_duration_ms = self.total_duration_ms
        
        # タイミング解析
        self._parse_timings(dialogue_matches)
    
    def _parse_timings(self, dialogue_matches: List[Tuple[str, str, str, str]]) -> None:
        """タイミング解析"""
        self.timings = []
        
        for line_index, (layer, start_time, end_time, text_with_tags) in enumerate(dialogue_matches):
            if int(layer) == 0:  # メイン行のみ処理
                # ASSタグを除去してクリーンなテキストを取得
                clean_text = self.remove_ass_tags(text_with_tags)
                
                # 時間をミリ秒に変換
                start_time_ms = ASSTimeUtils.to_milliseconds(start_time)
                end_time_ms = ASSTimeUtils.to_milliseconds(end_time)
                duration_ms = end_time_ms - start_time_ms
                
                timing = {self.class_name}Timing(
                    text=clean_text,
                    start_time_ms=start_time_ms,
                    end_time_ms=end_time_ms,
                    duration_ms=duration_ms,
                    line_index=line_index
                )
                self.timings.append(timing)
    
    def _get_timing_data_json(self) -> str:
        """タイミングデータのJSON文字列を返す"""
        timing_data = []
        for timing in self.timings:
            timing_data.append({{
                "text": timing.text,
                "start_time": timing.start_time_ms,
                "duration": timing.duration_ms,
                "line_index": timing.line_index
            }})
        
        return json.dumps(timing_data, ensure_ascii=False, indent=2)
    
    def _build_template_html(self) -> str:
        """テンプレート固有HTML"""
        html_parts = []
        html_parts.append(f'<div class="text-container" data-template="{self.category}">')
        
        for timing in self.timings:
            html_parts.append(
                f'    <div class="text-line" data-line="{{timing.line_index}}">{{timing.text}}</div>'
            )
        
        html_parts.append('</div>')
        return '\n'.join(html_parts)
    
    def _build_ui_elements_html(self) -> str:
        """UI要素HTML"""
        return """
    <div class="ui-overlay">
        <div class="control-panel">
            <button id="playPauseBtn" class="control-btn">▶️</button>
            <button id="resetBtn" class="control-btn">🔄</button>
            <div class="progress-bar">
                <div id="progressIndicator" class="progress-indicator"></div>
            </div>
        </div>
    </div>
        """
    
    def _get_template_title(self) -> str:
        """HTMLタイトルを返す"""
        return f"{self.class_name} Animation"
    
    def _get_responsive_css_class(self) -> str:
        """レスポンシブCSS用のクラス名を返す"""
        return "text-container"
    
    def _get_print_template_name(self) -> str:
        """ログ出力用のテンプレート名を返す"""
        return "{self.class_name}"
    
    def _get_data_count(self) -> int:
        """要素数を返す"""
        return len(self.timings)
    
    def _get_template_category(self) -> str:
        """テンプレートカテゴリを取得"""
        return "{self.category}"
    
    def _get_template_name(self) -> str:
        """テンプレート名を取得"""
        return "{self.template_name}"
'''
        
        # ファイル書き込み
        output_path = self.base_path / "src" / "scrollcast" / "conversion" / f"{self.template_name}_plugin_converter.py"
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(content, encoding='utf-8')
    
    def _generate_css_template(self) -> None:
        """CSSテンプレートを生成"""
        content = f'''/*
 * {self.class_name} Template CSS
 * {self.template_name} アニメーション効果
 */

/* Main container - follows scroll-cast naming standards */
.text-container[data-template="{self.category}"] {{
    position: fixed;
    top: 0;
    left: 0;
    width: 100vw;
    height: 100vh;
    background: #000;
    color: #fff;
    font-family: Arial, sans-serif;
    overflow: hidden;
}}

/* Text lines - JavaScript Plugin controls visibility */
.text-container[data-template="{self.category}"] .text-line {{
    display: none; /* 初期状態は非表示、JavaScriptで制御 */
    position: fixed;
    top: 50%;
    left: 50%;
    transform: translate(-50%, -50%);
    font-size: 2.5rem;
    line-height: 1.2;
    white-space: nowrap;
    font-weight: normal;
    opacity: 0;
    transition: opacity 0.3s ease-in-out;
}}

/* レスポンシブ対応 */
@media (max-width: 768px) {{
    .text-container[data-template="{self.category}"] .text-line {{
        font-size: 1.8rem;
    }}
}}

@media (max-width: 480px) {{
    .text-container[data-template="{self.category}"] .text-line {{
        font-size: 1.4rem;
    }}
}}

/* アニメーション効果 (TODO: テンプレート固有の効果を実装) */
.text-container[data-template="{self.category}"] .text-line.animating {{
    display: block;
    opacity: 1;
    /* TODO: テンプレート固有のアニメーション効果を追加 */
}}

/* CSS Override Architecture サポート - decoration hooks */
.text-line.decoration-enhanced {{
    /* 装飾システム用フック */
}}

.text-container[data-template="{self.category}"] .text-line.decoration-enhanced {{
    /* {self.template_name}固有の装飾フック */
}}

/* デバッグモード */
.text-container[data-template="{self.category}"].debug .text-line {{
    border: 1px solid rgba(255, 255, 255, 0.2);
    background: rgba(255, 255, 255, 0.05);
}}
'''
        
        # ディレクトリ作成とファイル書き込み
        output_path = self.base_path / "src" / "web" / "templates" / self.category / self.template_name / "sc-template.css"
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(content, encoding='utf-8')
    
    def _generate_javascript_plugin(self) -> None:
        """JavaScriptプラグインを生成"""
        content = f'''/*
 * ScrollCast {self.class_name} Display Plugin
 * {self.template_name} アニメーション表示プラグイン
 */

window.{self.class_name}DisplayPlugin = {{
    name: '{self.template_name}_display',
    
    initialize: function(config) {{
        this.config = config;
        this.lines = document.querySelectorAll('.text-line');
        this.setupDisplayHandlers();
        this.initializeDisplay();
    }},
    
    setupDisplayHandlers: function() {{
        window.addEventListener('sequence_start', (event) => {{
            this.playSequence(event.detail.index, event.detail.data);
        }});
    }},
    
    initializeDisplay: function() {{
        this.lines.forEach(line => {{
            line.style.display = 'none';
            line.style.opacity = '0';
            line.style.transform = 'translate(-50%, -50%)';
        }});
    }},
    
    playSequence: function(sequenceIndex, sequenceData) {{
        if (sequenceIndex >= this.lines.length) return;
        
        const line = this.lines[sequenceIndex];
        if (!line) return;
        
        this.animateTemplateLine(line, sequenceData);
    }},
    
    animateTemplateLine: function(line, sequenceData) {{
        // データ構造の互換性を保つ
        const duration = sequenceData.duration || sequenceData.total_duration || 8000;
        const durationMs = duration > 100 ? duration : duration * 1000;
        
        // 初期状態を設定
        line.style.display = 'block';
        line.style.opacity = '1';
        line.style.transform = 'translate(-50%, -50%)';
        
        // TODO: テンプレート固有のアニメーション効果を実装
        // 例: 下から上へのスクロール
        line.style.transform = 'translate(-50%, -50%) translateY(100vh)';
        
        setTimeout(() => {{
            const transitionDuration = durationMs / 1000;
            line.style.transition = `transform ${{transitionDuration}}s linear`;
            line.style.transform = 'translate(-50%, -50%) translateY(-100vh)';
            
            // アニメーション完了後のクリーンアップ
            setTimeout(() => {{
                line.style.display = 'none';
                line.style.transition = '';
                line.style.transform = '';
            }}, durationMs);
        }}, 50);
    }}
}};
'''
        
        # ファイル書き込み (src/web/pluginsディレクトリに配置)
        output_path = self.base_path / "src" / "web" / "plugins" / f"{self.template_name.replace('_', '-')}-display-plugin.js"
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(content, encoding='utf-8')
    
    def _generate_config_file(self) -> None:
        """設定ファイルを生成"""
        content = f'''template_name: {self.template_name}
version: 1.0.0
description: {self.template_name} animation effect
author: Template Generator
category: {self.category}
tags:
- animation
- {self.category}
- {self.template_name}

default_parameters:
  duration: 8.0
  delay: 0.5
  font_size: 64
  font_name: Arial

parameter_constraints: {{}}

# presets:
# - name: default
#   description: Default {self.template_name} animation
#   parameters:
#     duration: 8.0
#     delay: 0.5
#     font_size: 64
'''
        
        # ファイル書き込み
        output_path = self.base_path / "config" / f"{self.template_name}.yaml"
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(content, encoding='utf-8')
    
    def _update_template_engine(self) -> None:
        """template_engine.pyを更新"""
        engine_path = self.base_path / "src" / "scrollcast" / "orchestrator" / "template_engine.py"
        
        if not engine_path.exists():
            print(f"⚠️  Warning: template_engine.py not found at {engine_path}")
            return
        
        # 既存コンテンツを読み込み
        content = engine_path.read_text(encoding='utf-8')
        
        # import文を追加
        import_line = f"            from ..coloring.{self.template_name} import {self.class_name}Template"
        register_line = f"            self.register_template({self.class_name}Template())"
        
        # _register_builtin_templatesメソッドを探して追加
        if "_register_builtin_templates" in content:
            # 最後のregister_template呼び出しを探して、その後に追加
            lines = content.split('\n')
            modified_lines = []
            added = False
            
            for i, line in enumerate(lines):
                modified_lines.append(line)
                
                # 最後のregister_template呼び出しの後に追加
                if "self.register_template(" in line and not added:
                    # 次の行が空行またはexceptの場合、その前に追加
                    if i + 1 < len(lines) and (lines[i + 1].strip() == "" or "except" in lines[i + 1]):
                        # import文を追加
                        modified_lines.append("")
                        modified_lines.append("        try:")
                        modified_lines.append(import_line)
                        modified_lines.append(register_line)
                        modified_lines.append("        except ImportError as e:")
                        modified_lines.append(f'            print(f"Warning: Failed to import {self.class_name}Template: {{e}}")')
                        added = True
            
            if added:
                engine_path.write_text('\n'.join(modified_lines), encoding='utf-8')
                print(f"✅ Updated template_engine.py with {self.class_name}Template registration")
            else:
                print(f"⚠️  Warning: Could not automatically update template_engine.py")
        else:
            print(f"⚠️  Warning: _register_builtin_templates method not found in template_engine.py")
    
    def _update_hierarchical_converter(self) -> None:
        """hierarchical_template_converter.pyを更新"""
        converter_path = self.base_path / "src" / "scrollcast" / "conversion" / "hierarchical_template_converter.py"
        
        if not converter_path.exists():
            print(f"⚠️  Warning: hierarchical_template_converter.py not found at {converter_path}")
            return
        
        # 既存コンテンツを読み込み
        content = converter_path.read_text(encoding='utf-8')
        
        # import文を追加
        import_line = f"from .{self.template_name}_plugin_converter import {self.class_name}PluginConverter"
        
        # template_mappingに追加するエントリ
        mapping_entry = f'''            "{self.template_name}": {{
                "category": "{self.category}",
                "converter_class": {self.class_name}PluginConverter,
                "template_path": os.path.join(os.path.dirname(__file__), "..", "..", "web", "templates", "{self.category}", "{self.template_name}")
            }},'''
        
        # importセクションを更新
        if "from .revolver_up_plugin_converter import RevolverUpPluginConverter" in content:
            updated_content = content.replace(
                "from .revolver_up_plugin_converter import RevolverUpPluginConverter",
                f"from .revolver_up_plugin_converter import RevolverUpPluginConverter\n{import_line}"
            )
        else:
            print(f"⚠️  Warning: Could not find import section in hierarchical_template_converter.py")
            return
        
        # template_mappingを更新
        if '"revolver_up": {' in updated_content:
            # revolver_upエントリの後に追加
            pattern = r'("revolver_up": \{[^}]*\})'
            replacement = r'\1,\n' + mapping_entry
            updated_content = re.sub(pattern, replacement, updated_content, flags=re.DOTALL)
            
            converter_path.write_text(updated_content, encoding='utf-8')
            print(f"✅ Updated hierarchical_template_converter.py with {self.class_name}PluginConverter mapping")
        else:
            print(f"⚠️  Warning: Could not find template_mapping section in hierarchical_template_converter.py")


def main():
    """メイン関数"""
    if len(sys.argv) != 3:
        print("Usage: python template_generator.py <template_name> <category>")
        print("Categories: typewriter, railway, scroll")
        sys.exit(1)
    
    template_name = sys.argv[1]
    category = sys.argv[2]
    
    # テンプレート名の検証
    if not re.match(r'^[a-z][a-z0-9_]*$', template_name):
        print("❌ Error: Template name must be lowercase with underscores (e.g., my_template)")
        sys.exit(1)
    
    # カテゴリの検証
    if category not in ['typewriter', 'railway', 'scroll']:
        print("❌ Error: Category must be one of: typewriter, railway, scroll")
        sys.exit(1)
    
    # 既存テンプレートの重複チェック
    base_path = Path(__file__).parent.parent
    existing_file = base_path / "src" / "scrollcast" / "coloring" / f"{template_name}.py"
    if existing_file.exists():
        print(f"❌ Error: Template '{template_name}' already exists")
        sys.exit(1)
    
    # テンプレート生成
    generator = TemplateGenerator(template_name, category)
    generator.generate_all_files()
    
    print(f"")
    print(f"🎯 Next Steps:")
    print(f"1. Implement ASS effects in: src/scrollcast/coloring/{template_name}.py")
    print(f"2. Implement animation in: src/web/plugins/{template_name.replace('_', '-')}-display-plugin.js")
    print(f"3. Customize CSS styles in: src/web/templates/{category}/{template_name}/sc-template.css")
    print(f"4. Test with: PYTHONPATH=src python3 -m scrollcast.orchestrator.cli.main {template_name} 'Test'")


if __name__ == '__main__':
    main()