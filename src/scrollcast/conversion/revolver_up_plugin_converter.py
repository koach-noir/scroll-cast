"""
Revolver Up Plugin Converter
リボルバーアップアニメーション用プラグインコンバーター

アニメーション仕様:
- 文章がLINEごとに左寄せで縦に並ぶ
- 縦位置中央がカレント行（50%拡大）
- 文字数×0.3秒待機後、全体が上にスライド
- カレント行が次の行に移動
"""

import json
from typing import List, Dict, Any
from .plugin_converter_base import PluginConverterBase
from .plugin_system import TemplateConfig
from .utils import ASSDialogueParser, ASSTimeUtils


class RevolverUpPluginConverter(PluginConverterBase):
    """
    リボルバーアップアニメーション用プラグインコンバーター
    
    External JavaScript Reference Architecture を使用:
    - Template-based HTML generation
    - External asset deployment
    - Unified CSS class structure
    """
    
    def __init__(self):
        super().__init__()
        self.line_timings: List[Dict[str, Any]] = []
        
    def parse_ass_file(self, ass_file_path: str) -> None:
        """ASSファイルを解析してタイミングデータを抽出"""
        with open(ass_file_path, 'r', encoding='utf-8') as f:
            ass_content = f.read()
        
        parser = ASSDialogueParser()
        dialogues = parser.parse_dialogues(ass_content)
        
        self.line_timings = []
        
        for i, dialogue in enumerate(dialogues):
            # dialogue is a tuple: (layer, start_time, end_time, text_with_tags)
            layer, start_time_str, end_time_str, text_with_tags = dialogue
            
            # ASSタグを除去
            clean_text = self.remove_ass_tags(text_with_tags)
            
            # 時間をミリ秒に変換
            start_ms = ASSTimeUtils.to_milliseconds(start_time_str)
            end_ms = ASSTimeUtils.to_milliseconds(end_time_str)
            
            # 文字数に基づく表示時間計算 (0.3秒/文字)
            char_count = len(clean_text.strip())
            display_duration = max(char_count * 0.3 * 1000, 2000)  # 最低2秒
            slide_duration = 800  # スライドアニメーション時間
            
            line_data = {
                "line_index": i,
                "text": clean_text.strip(),
                "char_count": char_count,
                "start_time": start_ms,
                "display_duration": display_duration,
                "slide_duration": slide_duration,
                "total_duration": display_duration + slide_duration,
                "end_time": start_ms + display_duration + slide_duration
            }
            
            self.line_timings.append(line_data)
    
    def remove_ass_tags(self, text_with_tags: str) -> str:
        """ASSタグを除去"""
        import re
        return re.sub(r'\{[^}]*\}', '', text_with_tags).strip()
    
    def get_template_config(self) -> TemplateConfig:
        """テンプレート設定を返す"""
        return TemplateConfig(
            template_name="revolver_up",
            navigation_unit="line",
            required_plugins=[
                "auto_play",
                "revolver_up_display"
            ],
            plugin_configs={
                "auto_play": {
                    "auto_start": True,
                    "initial_delay": 500
                },
                "revolver_up_display": {
                    "element_selector": ".text-line",
                    "viewport_selector": ".revolver-viewport",
                    "char_display_duration": 0.3,
                    "slide_duration": 0.8,
                    "font_scale_factor": 1.5
                }
            }
        )
    
    def _get_template_name(self) -> str:
        """テンプレート名を返す"""
        return "revolver_up"
    
    def _get_template_category(self) -> str:
        """テンプレートカテゴリを返す"""
        return "scroll"
    
    def _build_content_html(self) -> str:
        """統一CSS クラス構造でコンテンツHTMLを生成"""
        content_parts = []
        
        for line_data in self.line_timings:
            line_html = (
                f'<div class="text-line" data-line="{line_data["line_index"]}">'
                f'{line_data["text"]}</div>'
            )
            content_parts.append(line_html)
        
        return '\n            '.join(content_parts)
    
    def _get_timing_data_json(self) -> str:
        """AutoPlayプラグイン用タイミングデータJSONを生成"""
        timing_entries = []
        
        for line_data in self.line_timings:
            timing_entries.append({
                "sequence_index": line_data["line_index"],
                "text": line_data["text"],
                "char_count": line_data["char_count"],
                "start_time": line_data["start_time"],
                "display_duration": line_data["display_duration"],
                "slide_duration": line_data["slide_duration"],
                "total_duration": line_data["total_duration"],
                "end_time": line_data["end_time"]
            })
        
        return json.dumps(timing_entries, ensure_ascii=False, indent=4)
    
    def _get_title(self) -> str:
        """ページタイトルを生成"""
        line_count = len(self.line_timings)
        return f"ScrollCast - Revolver Up Effect ({line_count} lines)"
    
    def _build_template_html(self) -> str:
        """テンプレート固有HTMLを構築 - simple_roleと同じシンプル構造"""
        return f'<div class="text-container" data-template="scroll">{self._build_content_html()}</div>'
    
    def _build_ui_elements_html(self) -> str:
        """UI要素HTML（リボルバーアップは基本UI不要）"""
        return ""
    
    def _get_template_title(self) -> str:
        """HTMLタイトルを返す"""
        return self._get_title()
    
    def _get_responsive_css_class(self) -> str:
        """レスポンシブCSS用のクラス名を返す"""
        return "revolver-up-responsive"
    
    def _get_print_template_name(self) -> str:
        """ログ出力用のテンプレート名を返す"""
        return "revolver_up"
    
    def _get_data_count(self) -> int:
        """要素数を返す"""
        return len(self.line_timings)