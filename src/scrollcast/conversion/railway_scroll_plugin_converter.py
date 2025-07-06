"""
RailwayScroll Plugin-based ASS to HTML converter
プラグイン型RailwayScrollテンプレート実装
"""

import json
from typing import List, Tuple, NamedTuple
from .utils import ASSTimeUtils, ASSMetadataExtractor, ASSDialogueParser
from .plugin_system import TemplateConfig
from .plugin_converter_base import PluginConverterBase


class RailwayScrollTiming(NamedTuple):
    """Railway_Scrollのタイミング情報"""
    text: str
    fade_in_start_ms: int    # Layer 0: 下→中央移動開始
    fade_in_end_ms: int      # Layer 0: 下→中央移動完了
    static_start_ms: int     # Layer 1: 中央静止開始
    static_end_ms: int       # Layer 1: 中央静止終了
    fade_out_start_ms: int   # Layer 2: 中央→上移動開始
    fade_out_end_ms: int     # Layer 2: 中央→上移動完了
    line_number: int         # 行番号


class RailwayScrollPluginConverter(PluginConverterBase):
    """プラグイン型RailwayScroll ASS→HTML変換クラス"""
    
    def __init__(self):
        super().__init__()
        self.line_timings: List[RailwayScrollTiming] = []
    
    def get_template_config(self) -> TemplateConfig:
        """RailwayScrollテンプレートのプラグイン設定（シンプルテキストフロー版）"""
        return TemplateConfig(
            template_name="railway_scroll",
            navigation_unit="line",
            required_plugins=["auto_play", "railway_display"],
            plugin_configs={
                "auto_play": {
                    "auto_start": True,
                    "initial_delay": 500
                },
                "railway_display": {
                    "element_selector": ".text-line",
                    "animation_duration": 800
                }
            }
        )
    
    def parse_ass_file(self, ass_file_path: str) -> None:
        """ASSファイルを解析"""
        content = self.read_ass_file_content(ass_file_path)
        
        # メタデータ抽出
        self.metadata = ASSMetadataExtractor.extract_metadata(content, "Railway_Scroll")
        
        # Dialogue行の抽出と総時間計算
        dialogue_matches = ASSDialogueParser.parse_dialogues(content)
        self.total_duration_ms = ASSDialogueParser.calculate_total_duration(dialogue_matches)
        self.metadata.total_duration_ms = self.total_duration_ms
        
        # RailwayScroll固有のタイミング解析
        self._parse_railway_scroll_layers(dialogue_matches)
    
    def _parse_railway_scroll_layers(self, dialogue_matches: List[Tuple[str, str, str, str]]) -> None:
        """Railway_Scrollの3層レイヤー構造を解析"""
        # テキストごとにレイヤー情報をグループ化
        text_groups = {}
        
        for layer, start_time, end_time, text_with_tags in dialogue_matches:
            # テキスト内容を抽出（ASSタグを除去）
            text_content = self.remove_ass_tags(text_with_tags)
            
            if not text_content:
                continue
            
            layer_num = int(layer)
            start_ms = ASSTimeUtils.to_milliseconds(start_time)
            end_ms = ASSTimeUtils.to_milliseconds(end_time)
            
            if text_content not in text_groups:
                text_groups[text_content] = {}
            
            text_groups[text_content][layer_num] = {
                'start_ms': start_ms,
                'end_ms': end_ms,
                'tags': text_with_tags
            }
        
        # 各テキストの3層タイミングを統合
        line_number = 0
        for text_content, layers in text_groups.items():
            if 0 in layers and 1 in layers and 2 in layers:
                # 完全な3層構造がある場合
                layer0 = layers[0]  # フェードイン (下→中央)
                layer1 = layers[1]  # 静止表示 (中央)
                layer2 = layers[2]  # フェードアウト (中央→上)
                
                timing = RailwayScrollTiming(
                    text=text_content,
                    fade_in_start_ms=layer0['start_ms'],
                    fade_in_end_ms=layer0['end_ms'],
                    static_start_ms=layer1['start_ms'],
                    static_end_ms=layer1['end_ms'],
                    fade_out_start_ms=layer2['start_ms'],
                    fade_out_end_ms=layer2['end_ms'],
                    line_number=line_number
                )
                
                self.line_timings.append(timing)
                line_number += 1
        
        # 開始時間順にソート
        self.line_timings.sort(key=lambda x: x.fade_in_start_ms)
    
    def _get_timing_data_json(self) -> str:
        """タイミングデータのJSON文字列を返す"""
        timing_data = []
        
        for i, timing in enumerate(self.line_timings):
            # JavaScriptで使用するタイミングデータ
            timing_data.append({
                'text': timing.text,
                'start_time': timing.fade_in_start_ms,  # 絶対開始時間（auto-playプラグイン用）
                'fade_in_start': 0,  # 相対時間での開始は0
                'fade_in_duration': timing.fade_in_end_ms - timing.fade_in_start_ms,
                'static_start': timing.static_start_ms - timing.fade_in_start_ms,
                'static_duration': timing.static_end_ms - timing.static_start_ms,
                'fade_out_start': timing.fade_out_start_ms - timing.fade_in_start_ms,
                'fade_out_duration': timing.fade_out_end_ms - timing.fade_out_start_ms,
                'total_duration': timing.fade_out_end_ms - timing.fade_in_start_ms
            })
        
        return json.dumps(timing_data)
    
    def _build_template_html(self) -> str:
        """テンプレート固有HTML（Template-Based Generation）"""
        # Template file path
        template_path = "src/templates/railway/railway_scroll/sc-template.html"
        
        # Load template content
        template_content = self._load_template_file(template_path)
        
        # Generate lines HTML with common selectors
        lines_html = []
        for i, timing in enumerate(self.line_timings):
            lines_html.append(
                f'<div class="text-line" data-line="{i}">{timing.text}</div>'
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
            for i, timing in enumerate(self.line_timings):
                lines_html.append(
                    f'<div class="text-line" data-line="{i}">{timing.text}</div>'
                )
            content_html = '\n        '.join(lines_html)
            return f"""    <div class="text-container" data-template="railway">
        {content_html}
    </div>"""
    
    def _build_ui_elements_html(self) -> str:
        """UI要素HTML"""
        from .utils import HTMLTemplateBuilder
        return HTMLTemplateBuilder.build_ui_elements_html("行", "鉄道方向幕風スクロール")
    
    def _get_template_title(self) -> str:
        """HTMLタイトルを返す"""
        return "ScrollCast - Railway Scroll Effect (Plugin)"
    
    def _get_responsive_css_class(self) -> str:
        """レスポンシブCSS用のクラス名を返す"""
        return "text-container[data-template=\"railway\"]"
    
    def _get_print_template_name(self) -> str:
        """ログ出力用のテンプレート名を返す"""
        return "Railway Scroll Effect (Plugin)"
    
    def _get_data_count(self) -> int:
        """要素数を返す"""
        return len(self.line_timings)
    
    
