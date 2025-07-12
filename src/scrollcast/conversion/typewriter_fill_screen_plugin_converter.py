"""
TypewriterFillScreen Plugin-based ASS to HTML converter
プラグイン型TypewriterFillScreenテンプレート実装
"""

import re
import json
from typing import List, Tuple, NamedTuple
from .utils import ASSTimeUtils, ASSMetadataExtractor, ASSDialogueParser
from .plugin_system import TemplateConfig
from .plugin_converter_base import PluginConverterBase


class TypewriterFillScreenTiming(NamedTuple):
    """タイミング情報"""
    text: str
    start_time_ms: int
    end_time_ms: int
    duration_ms: int
    line_index: int


class TypewriterFillScreenPluginConverter(PluginConverterBase):
    """プラグイン型TypewriterFillScreen ASS→HTML変換クラス"""
    
    def __init__(self):
        super().__init__()
        self.timings: List[TypewriterFillScreenTiming] = []
    
    def get_template_config(self) -> TemplateConfig:
        """TypewriterFillScreenテンプレートのプラグイン設定"""
        return TemplateConfig(
            template_name="typewriter_fill_screen",
            navigation_unit="line",
            required_plugins=["auto_play", "typewriter_fill_screen_display"],
            plugin_configs={
                "auto_play": {
                    "auto_start": True,
                    "initial_delay": 500
                },
                "typewriter_fill_screen_display": {
                    "element_selector": ".text-line"
                }
            }
        )
    
    def parse_ass_file(self, ass_file_path: str) -> None:
        """ASSファイルを解析"""
        content = self.read_ass_file_content(ass_file_path)
        
        # メタデータ抽出
        self.metadata = ASSMetadataExtractor.extract_metadata(content, "TypewriterFillScreen")
        
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
                
                timing = TypewriterFillScreenTiming(
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
            timing_data.append({
                "text": timing.text,
                "start_time": timing.start_time_ms,
                "duration": timing.duration_ms,
                "line_index": timing.line_index
            })
        
        return json.dumps(timing_data, ensure_ascii=False, indent=2)
    
    def _build_template_html(self) -> str:
        """テンプレート固有HTML"""
        html_parts = []
        html_parts.append(f'<div class="text-container" data-template="typewriter">')
        
        for timing in self.timings:
            html_parts.append(
                f'    <div class="text-line" data-line="{timing.line_index}">{timing.text}</div>'
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
        return f"TypewriterFillScreen Animation"
    
    def _get_responsive_css_class(self) -> str:
        """レスポンシブCSS用のクラス名を返す"""
        return "text-container"
    
    def _get_print_template_name(self) -> str:
        """ログ出力用のテンプレート名を返す"""
        return "TypewriterFillScreen"
    
    def _get_data_count(self) -> int:
        """要素数を返す"""
        return len(self.timings)
    
    def _get_template_category(self) -> str:
        """テンプレートカテゴリを取得"""
        return "typewriter"
    
    def _get_template_name(self) -> str:
        """テンプレート名を取得"""
        return "typewriter_fill_screen"
