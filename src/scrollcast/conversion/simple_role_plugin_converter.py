"""
SimpleRole Plugin-based ASS to HTML converter
プラグイン型SimpleRoleテンプレート実装（標準フロー準拠）
"""

import json
from typing import List, Tuple, NamedTuple
from .utils import ASSTimeUtils, ASSMetadataExtractor, ASSDialogueParser
from .plugin_system import TemplateConfig
from .plugin_converter_base import PluginConverterBase


class SimpleRoleTiming(NamedTuple):
    """SimpleRoleのタイミング情報"""
    text: str
    start_ms: int
    end_ms: int
    line_number: int


class SimpleRolePluginConverter(PluginConverterBase):
    """プラグイン型SimpleRole ASS→HTML変換クラス"""
    
    def __init__(self):
        super().__init__()
        self.line_timings: List[SimpleRoleTiming] = []
    
    def get_template_config(self) -> TemplateConfig:
        """SimpleRoleテンプレートのプラグイン設定（シンプルテキストフロー版）"""
        return TemplateConfig(
            template_name="simple_role",
            navigation_unit="line",
            required_plugins=["auto_play", "simple_role_display"],
            plugin_configs={
                "auto_play": {
                    "auto_start": True,
                    "initial_delay": 1000
                },
                "simple_role_display": {
                    "element_selector": ".text-line",
                    "scroll_duration": 8000,
                    "continuous_display": True,
                    "fade_effect": True
                }
            }
        )
    
    def parse_ass_file(self, ass_file_path: str) -> None:
        """ASSファイルを解析"""
        content = self.read_ass_file_content(ass_file_path)
        
        # メタデータ抽出
        self.metadata = ASSMetadataExtractor.extract_metadata(content, "Simple_Role")
        
        # Dialogue行の抽出と総時間計算
        dialogue_matches = ASSDialogueParser.parse_dialogues(content)
        self.total_duration_ms = ASSDialogueParser.calculate_total_duration(dialogue_matches)
        self.metadata.total_duration_ms = self.total_duration_ms
        
        # SimpleRole固有のタイミング解析
        self._parse_simple_role_timings(dialogue_matches)
    
    def _parse_simple_role_timings(self, dialogue_matches: List[Tuple[str, str, str, str]]) -> None:
        """SimpleRole固有のタイミング解析"""
        self.line_timings = []
        line_number = 0
        
        for layer, start_time, end_time, text_with_tags in dialogue_matches:
            # Layer 0のみ処理
            if int(layer) == 0:
                # テキスト内容を抽出（ASSタグを除去）
                text_content = self.remove_ass_tags(text_with_tags)
                
                if not text_content:
                    continue
                
                start_ms = ASSTimeUtils.to_milliseconds(start_time)
                end_ms = ASSTimeUtils.to_milliseconds(end_time)
                
                timing = SimpleRoleTiming(
                    text=text_content,
                    start_ms=start_ms,
                    end_ms=end_ms,
                    line_number=line_number
                )
                
                self.line_timings.append(timing)
                line_number += 1
        
        # 開始時間順にソート
        self.line_timings.sort(key=lambda x: x.start_ms)
    
    def _get_timing_data_json(self) -> str:
        """タイミングデータのJSON文字列を返す"""
        timing_data = []
        
        for timing in self.line_timings:
            timing_data.append({
                'text': timing.text,
                'start_time': timing.start_ms,
                'duration': timing.end_ms - timing.start_ms,
                'line_index': timing.line_number
            })
        
        return json.dumps(timing_data)
    
    def _build_template_html(self) -> str:
        """テンプレート固有HTML（Template-Based Generation）"""
        # Template file path
        template_path = "src/templates/scroll/scroll_role/sc-template.html"
        
        # Load template content
        template_content = self._load_template_file(template_path)
        
        # Generate lines HTML with common selectors
        lines_html = []
        for timing in self.line_timings:
            lines_html.append(
                f'<div class="text-line" data-line="{timing.line_number}">{timing.text}</div>'
            )
        
        lines_content = '\n        '.join(lines_html)
        
        # Replace placeholder with generated content
        return template_content.replace('{{LINES_HTML}}', lines_content)
    
    def _load_template_file(self, template_path: str) -> str:
        """Load template file content"""
        import os
        try:
            with open(template_path, 'r', encoding='utf-8') as f:
                return f.read()
        except FileNotFoundError:
            # Fallback to legacy generation if template not found
            lines_html = []
            for timing in self.line_timings:
                lines_html.append(
                    f'<div class="text-line" data-line="{timing.line_number}">{timing.text}</div>'
                )
            content_html = '\n        '.join(lines_html)
            return f"""    <div class="text-container" data-template="scroll">
        {content_html}
    </div>"""
    
    def _build_ui_elements_html(self) -> str:
        """UI要素HTML"""
        from .utils import HTMLTemplateBuilder
        return HTMLTemplateBuilder.build_ui_elements_html("行", "シンプルロール（エンドロール風）")
    
    def _get_template_title(self) -> str:
        """HTMLタイトルを返す"""
        return "ScrollCast - Simple Role Effect (Plugin)"
    
    def _get_responsive_css_class(self) -> str:
        """レスポンシブCSS用のクラス名を返す"""
        return "text-container[data-template=\"scroll\"]"
    
    def _get_print_template_name(self) -> str:
        """ログ出力用のテンプレート名を返す"""
        return "Simple Role Effect (Plugin)"
    
    def _get_data_count(self) -> int:
        """要素数を返す"""
        return len(self.line_timings)
    
    
