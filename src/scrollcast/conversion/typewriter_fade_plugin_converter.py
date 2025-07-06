"""
TypewriterFade Plugin-based ASS to HTML converter
プラグイン型TypewriterFadeテンプレート実装
"""

import re
import json
from typing import List, Tuple, NamedTuple
from .utils import ASSTimeUtils, ASSMetadataExtractor, ASSDialogueParser
from .plugin_system import TemplateConfig
from .plugin_converter_base import PluginConverterBase


class CharacterTiming(NamedTuple):
    """文字とそのタイミング情報"""
    char: str
    fade_start_ms: int
    fade_end_ms: int
    scroll_position: float  # 0.0 - 1.0
    y_position: int  # Y座標位置
    line_number: int  # 行番号
    dialogue_start_ms: int  # Dialogue開始時間
    dialogue_end_ms: int    # Dialogue終了時間


class TypewriterFadePluginConverter(PluginConverterBase):
    """プラグイン型TypewriterFade ASS→HTML変換クラス"""
    
    def __init__(self):
        super().__init__()
        self.character_timings: List[CharacterTiming] = []
    
    def get_template_config(self) -> TemplateConfig:
        """TypewriterFadeテンプレートのプラグイン設定（シンプルテキストフロー版）"""
        return TemplateConfig(
            template_name="typewriter_fade",
            navigation_unit="sentence",
            required_plugins=["auto_play", "typewriter_display"],
            plugin_configs={
                "auto_play": {
                    "auto_start": True,
                    "initial_delay": 500
                },
                "typewriter_display": {
                    "element_selector": ".text-sentence, .typewriter-sentence",
                    "char_selector": ".text-char, .typewriter-char"
                }
            }
        )
    
    def parse_ass_file(self, ass_file_path: str) -> None:
        """ASSファイルを解析"""
        content = self.read_ass_file_content(ass_file_path)
        
        # メタデータ抽出
        self.metadata = ASSMetadataExtractor.extract_metadata(content, "Typewriter_Fade")
        
        # Dialogue行の抽出と総時間計算
        dialogue_matches = ASSDialogueParser.parse_dialogues(content)
        self.total_duration_ms = ASSDialogueParser.calculate_total_duration(dialogue_matches)
        self.metadata.total_duration_ms = self.total_duration_ms
        
        # TypewriterFade固有のタイミング解析
        self._parse_typewriter_timings(dialogue_matches)
    
    def _parse_typewriter_timings(self, dialogue_matches: List[Tuple[str, str, str, str]]) -> None:
        """TypewriterFade固有のタイミング解析"""
        self.character_timings = []
        dialogue_line_index = 0
        
        for layer, start_time, end_time, text_with_tags in dialogue_matches:
            # レイヤー0のみ処理（レイヤー1は空行用のため）
            if int(layer) == 0:
                line_timings = self._parse_character_timings_with_position(
                    text_with_tags, start_time, end_time, dialogue_line_index
                )
                self.character_timings.extend(line_timings)
                dialogue_line_index += 1
    
    def _parse_character_timings_with_position(self, text_with_tags: str, 
                                             start_time: str, end_time: str, 
                                             dialogue_line_index: int = 0) -> List[CharacterTiming]:
        """ASSタグ付きテキストから文字とタイミング・位置情報を抽出"""
        # Y位置を抽出
        pos_match = re.search(r'\\pos\((\d+),(\d+)\)', text_with_tags)
        y_position = int(pos_match.group(2)) if pos_match else 960
        
        # 行番号はDialogue行のシーケンス番号を使用
        line_number = dialogue_line_index
        
        # 開始・終了時間をミリ秒に変換
        start_time_ms = ASSTimeUtils.to_milliseconds(start_time)
        end_time_ms = ASSTimeUtils.to_milliseconds(end_time)
        
        # パターン: {\k15\alpha&HFF&\t(150,250,\alpha&H00&)}e
        pattern = r'\{[^}]*\\t\((\d+),(\d+),[^)]*\)\}(.)'
        matches = re.findall(pattern, text_with_tags)
        
        character_timings = []
        for fade_start, fade_end, char in matches:
            fade_start_ms = start_time_ms + int(fade_start)
            fade_end_ms = start_time_ms + int(fade_end)
            
            # スクロール位置を計算
            scroll_position = fade_end_ms / self.metadata.total_duration_ms if self.metadata.total_duration_ms > 0 else 0
            
            character_timings.append(CharacterTiming(
                char=char,
                fade_start_ms=fade_start_ms,
                fade_end_ms=fade_end_ms,
                scroll_position=scroll_position,
                y_position=y_position,
                line_number=line_number,
                dialogue_start_ms=start_time_ms,
                dialogue_end_ms=end_time_ms
            ))
        
        return character_timings
    
    def _get_timing_data_json(self) -> str:
        """タイミングデータのJSON文字列を返す"""
        # 行番号でグループ化
        sentences_dict = {}
        
        for timing in self.character_timings:
            line_number = timing.line_number
            if line_number not in sentences_dict:
                sentences_dict[line_number] = []
            sentences_dict[line_number].append(timing)
        
        # 開始時間順にソート
        sorted_sentences = sorted(sentences_dict.items(), key=lambda x: min(t.fade_start_ms for t in x[1]))
        
        # タイミングデータを生成
        sentences_timing_data = []
        
        for sentence_id, (line_number, char_timings) in enumerate(sorted_sentences):
            sorted_chars = sorted(char_timings, key=lambda x: x.fade_start_ms)
            char_timing_data = []
            
            for timing in sorted_chars:
                # 相対タイミング計算（Dialogue開始からの相対時間）
                relative_start = timing.fade_start_ms - timing.dialogue_start_ms
                relative_end = timing.fade_end_ms - timing.dialogue_start_ms
                char_timing_data.append({
                    'start': relative_start,
                    'end': relative_end,
                    'fade_duration': relative_end - relative_start
                })
            
            # Dialogue全体のタイミング情報を追加
            dialogue_start = char_timings[0].dialogue_start_ms
            dialogue_end = char_timings[0].dialogue_end_ms
            sentences_timing_data.append({
                'start_time': dialogue_start,  # 絶対開始時間（auto-playプラグイン用）
                'dialogue_start': dialogue_start,
                'dialogue_end': dialogue_end,
                'dialogue_duration': dialogue_end - dialogue_start,
                'chars': char_timing_data
            })
        
        return json.dumps(sentences_timing_data)
    
    def _build_template_html(self) -> str:
        """テンプレート固有HTML"""
        # 行番号でグループ化
        sentences_dict = {}
        
        for timing in self.character_timings:
            line_number = timing.line_number
            if line_number not in sentences_dict:
                sentences_dict[line_number] = []
            sentences_dict[line_number].append(timing)
        
        # 開始時間順にソート
        sorted_sentences = sorted(sentences_dict.items(), key=lambda x: min(t.fade_start_ms for t in x[1]))
        
        # 文ごとのHTML要素を生成
        sentences_html = []
        char_id = 0
        
        for sentence_id, (line_number, char_timings) in enumerate(sorted_sentences):
            # 文字を開始時間順にソート
            sorted_chars = sorted(char_timings, key=lambda x: x.fade_start_ms)
            sentence_chars = []
            
            for timing in sorted_chars:
                sentence_chars.append(
                    f'<span class="text-char typewriter-char" data-char-index="{len(sentence_chars)}" id="char-{char_id}">{timing.char}</span>'
                )
                char_id += 1
            
            sentences_html.append(
                f'<div class="text-sentence typewriter-sentence" data-sentence="{sentence_id}">{"".join(sentence_chars)}</div>'
            )
        
        content_html = '\n        '.join(sentences_html)
        return f"""    <div class="typewriter-container">
        {content_html}
    </div>"""
    
    def _build_ui_elements_html(self) -> str:
        """UI要素HTML"""
        from .utils import HTMLTemplateBuilder
        return HTMLTemplateBuilder.build_ui_elements_html("文", "タイプライター風フェード")
    
    def _get_template_title(self) -> str:
        """HTMLタイトルを返す"""
        return "ScrollCast - TypeWriter Effect (Plugin)"
    
    def _get_responsive_css_class(self) -> str:
        """レスポンシブCSS用のクラス名を返す"""
        return "typewriter-container"
    
    def _get_print_template_name(self) -> str:
        """ログ出力用のテンプレート名を返す"""
        return "TypeWriter Effect (Plugin)"
    
    def _get_data_count(self) -> int:
        """要素数を返す"""
        return len(self.character_timings)
    
    
