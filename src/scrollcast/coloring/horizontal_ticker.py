"""
Horizontal Ticker Template (New Architecture)
水平ティッカー（ニュース速報風）エフェクト - ASS生成特化版
"""

from typing import List
from dataclasses import dataclass
from .base import BaseTemplate, SubtitleTemplate, TemplateParameter, TimingInfo
from ..boxing import FormattedText


@dataclass
class HorizontalTickerTimingInfo(TimingInfo):
    """HorizontalTicker用タイミング情報"""
    text: str = ""
    style_overrides: dict = None
    metadata: dict = None
    
    def __post_init__(self):
        if self.style_overrides is None:
            self.style_overrides = {}
        if self.metadata is None:
            self.metadata = {}


class HorizontalTickerTemplate(BaseTemplate):
    """水平ティッカー（ニュース速報風）エフェクトテンプレート（ASS生成特化）"""
    
    @property
    def template_info(self) -> SubtitleTemplate:
        return SubtitleTemplate(
            name="horizontal_ticker",
            description="水平ティッカー（右→左 ニュース速報風連続表示）",
            parameters={
                "scroll_speed": TemplateParameter(
                    name="scroll_speed",
                    type=float,
                    default=1.0,
                    description="スクロール速度倍率",
                    min_value=0.3,
                    max_value=3.0
                ),
                "text_spacing": TemplateParameter(
                    name="text_spacing",
                    type=float,
                    default=2.0,
                    description="テキスト区切り間隔（画面幅倍率）",
                    min_value=1.0,
                    max_value=5.0
                ),
                "font_size": TemplateParameter(
                    name="font_size",
                    type=int,
                    default=48,
                    description="フォントサイズ",
                    min_value=24,
                    max_value=96
                ),
                "loop_behavior": TemplateParameter(
                    name="loop_behavior",
                    type=str,
                    default="continuous",
                    description="ループ動作（continuous/stop）",
                    allowed_values=["continuous", "stop"]
                ),
                "fade_edges": TemplateParameter(
                    name="fade_edges",
                    type=bool,
                    default=True,
                    description="画面端でのフェード効果"
                ),
                "ticker_duration": TemplateParameter(
                    name="ticker_duration",
                    type=float,
                    default=10.0,
                    description="1回の横断時間（秒）",
                    min_value=5.0,
                    max_value=30.0
                )
            }
        )
    
    def _calculate_text_width_estimate(self, text: str, font_size: int) -> float:
        """テキスト幅の概算計算（ピクセル単位）"""
        # ASCII文字とマルチバイト文字の大まかな幅計算
        ascii_count = sum(1 for c in text if ord(c) < 128)
        multibyte_count = len(text) - ascii_count
        
        # フォントサイズに基づく概算幅
        ascii_width = ascii_count * (font_size * 0.6)
        multibyte_width = multibyte_count * font_size
        
        return ascii_width + multibyte_width
    
    def generate_timing_data(self, formatted_texts: List[FormattedText], **kwargs) -> List[HorizontalTickerTimingInfo]:
        """HorizontalTicker用タイミングデータ生成"""
        # パラメータ取得
        scroll_speed = kwargs.get('scroll_speed', 1.0)
        text_spacing = kwargs.get('text_spacing', 2.0)
        ticker_duration = kwargs.get('ticker_duration', 10.0)
        font_size = kwargs.get('font_size', 48)
        loop_behavior = kwargs.get('loop_behavior', 'continuous')
        
        # 画面幅（1080p基準）
        screen_width = 1080
        
        # 実際のスクロール時間
        actual_duration = ticker_duration / scroll_speed
        
        timing_data = []
        
        # すべてのFormattedTextからテキスト行を連結
        all_text_lines = []
        for formatted_text in formatted_texts:
            all_text_lines.extend(formatted_text.get_text_lines())
        
        if not all_text_lines:
            return timing_data
        
        # テキスト間のスペーシング計算
        spacing_width = screen_width * text_spacing
        
        # 連続表示の場合は全テキストを連結
        if loop_behavior == "continuous":
            # テキストを区切り文字で連結
            separator = " • "  # ニュース風区切り
            combined_text = separator.join(all_text_lines)
            
            # テキスト幅計算
            text_width = self._calculate_text_width_estimate(combined_text, font_size)
            
            # 開始位置（画面右端から開始）
            start_x = screen_width + 100
            # 終了位置（テキスト全体が画面左端に消えるまで）
            end_x = -text_width - 100
            
            # 移動距離
            move_distance = start_x - end_x
            
            timing_info = HorizontalTickerTimingInfo(
                start_time=0.0,
                end_time=actual_duration,
                text=combined_text,
                style_overrides={
                    'alignment': 7,  # 左揃え
                    'margin_v': 960,  # 1080pの中央
                    'layer': 0,
                    'effect': 'horizontal_ticker_scroll'
                },
                metadata={
                    'scroll_speed': scroll_speed,
                    'text_width': text_width,
                    'move_distance': move_distance,
                    'start_x': start_x,
                    'end_x': end_x,
                    'loop_behavior': loop_behavior
                }
            )
            
            timing_data.append(timing_info)
        
        else:  # stop behavior
            # 各行を個別に処理（順次表示）
            current_time = 0.0
            
            for i, line_text in enumerate(all_text_lines):
                text_width = self._calculate_text_width_estimate(line_text, font_size)
                
                start_x = screen_width + 100
                end_x = -text_width - 100
                
                timing_info = HorizontalTickerTimingInfo(
                    start_time=current_time,
                    end_time=current_time + actual_duration,
                    text=line_text,
                    style_overrides={
                        'alignment': 7,
                        'margin_v': 960,
                        'layer': 0,
                        'effect': 'horizontal_ticker_scroll'
                    },
                    metadata={
                        'line_index': i,
                        'scroll_speed': scroll_speed,
                        'text_width': text_width,
                        'start_x': start_x,
                        'end_x': end_x,
                        'loop_behavior': loop_behavior
                    }
                )
                
                timing_data.append(timing_info)
                
                # 次の行は前の行の開始から一定時間後
                current_time += actual_duration * 0.1  # 重複を避けるため
        
        return timing_data
    
    def generate_ass_dialogue_lines(self, timing_data: List[HorizontalTickerTimingInfo], **kwargs) -> List[str]:
        """ASS Dialogue行生成（HorizontalTicker固有）"""
        font_size = kwargs.get('font_size', 48)
        fade_edges = kwargs.get('fade_edges', True)
        
        dialogue_lines = []
        
        for timing in timing_data:
            start_time = self._format_time(timing.start_time)
            end_time = self._format_time(timing.end_time)
            
            # 移動時間（ミリ秒）
            duration_ms = int((timing.end_time - timing.start_time) * 1000)
            
            # 開始・終了位置
            start_x = timing.metadata.get('start_x', 1080)
            end_x = timing.metadata.get('end_x', -500)
            
            # Y位置（画面中央下部）
            y_pos = 1600  # 画面下部にティッカーを配置
            
            # HorizontalTicker用ASSタグ
            ass_tags = [
                f"\\pos({start_x},{y_pos})",
                f"\\fs{font_size}",
                f"\\an7",  # 左上基準
                f"\\c&HFFFFFF&",  # 白色
                f"\\3c&H000000&",  # 黒アウトライン
                f"\\bord2",  # アウトライン太さ
                f"\\move({start_x},{y_pos},{end_x},{y_pos},0,{duration_ms})"
            ]
            
            # エッジフェード効果
            if fade_edges:
                # 画面端でのフェードアウト効果
                fade_start = int(duration_ms * 0.9)  # 90%地点からフェード開始
                ass_tags.append(f"\\t({fade_start},{duration_ms},\\alpha&HFF&)")
            
            ass_text = "{" + "".join(ass_tags) + "}" + timing.text
            
            dialogue_line = (
                f"Dialogue: {timing.style_overrides.get('layer', 0)},"
                f"{start_time},{end_time},"
                f"Default,,0,0,0,,"
                f"{ass_text}"
            )
            
            dialogue_lines.append(dialogue_line)
        
        return dialogue_lines
    
    def _format_time(self, seconds: float) -> str:
        """秒をASS時間形式に変換"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = seconds % 60
        return f"{hours}:{minutes:02d}:{secs:05.2f}"
    
    def generate_ass_from_formatted(self, formatted_text: FormattedText, **kwargs) -> str:
        """整形済みテキストからASS字幕を生成"""
        # タイミングデータ生成
        timing_data = self.generate_timing_data([formatted_text], **kwargs)
        
        # ASSヘッダー生成
        resolution = kwargs.get('resolution', (1080, 1920))
        header = self.generate_ass_header(resolution, **kwargs)
        
        # Dialogue行生成
        dialogue_lines = self.generate_ass_dialogue_lines(timing_data, **kwargs)
        
        # 完全なASS内容を組み立て
        ass_content = header + "\n[Events]\n"
        ass_content += "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text\n"
        
        for dialogue in dialogue_lines:
            ass_content += dialogue + "\n"
        
        return ass_content
    
    def calculate_total_duration(self, formatted_text: FormattedText, **kwargs) -> float:
        """総再生時間を計算"""
        scroll_speed = kwargs.get('scroll_speed', 1.0)
        ticker_duration = kwargs.get('ticker_duration', 10.0)
        loop_behavior = kwargs.get('loop_behavior', 'continuous')
        
        # テキスト行数
        lines = formatted_text.get_text_lines()
        num_lines = len(lines)
        
        if num_lines == 0:
            return 0.0
        
        # 実際のスクロール時間
        actual_duration = ticker_duration / scroll_speed
        
        if loop_behavior == "continuous":
            # 連続表示の場合は1回の横断時間
            return actual_duration
        else:
            # 停止モードの場合は行数に応じて時間延長
            return actual_duration * (1 + (num_lines - 1) * 0.1)