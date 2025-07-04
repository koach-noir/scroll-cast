"""
ASS Builder
ASSファイル構築のためのユーティリティ
"""

import os
from typing import Dict, Any, Optional, List


class ASSBuilder:
    """ASSファイル構築クラス"""
    
    def __init__(self, title: str = "Subtitle Video", resolution: tuple = (1080, 1920)):
        """
        Args:
            title: 動画タイトル
            resolution: 解像度 (width, height)
        """
        self.title = title
        self.width, self.height = resolution
        self.styles = {}
        self.events = []
    
    def add_style(self, name: str, font_name: str = "Arial", font_size: int = 64,
                  primary_color: str = "&H00FFFFFF", secondary_color: str = "&H000000FF",
                  outline_color: str = "&H00000000", back_color: str = "&H80000000",
                  bold: int = 1, italic: int = 0, underline: int = 0, strikeout: int = 0,
                  scale_x: int = 100, scale_y: int = 100, spacing: int = 0, angle: int = 0,
                  border_style: int = 1, outline: int = 3, shadow: int = 0, alignment: int = 5,
                  margin_l: int = 60, margin_r: int = 60, margin_v: int = 60, encoding: int = 1):
        """スタイルを追加
        
        Args:
            name: スタイル名
            font_name: フォント名
            font_size: フォントサイズ
            primary_color: プライマリカラー（16進数）
            secondary_color: セカンダリカラー
            outline_color: アウトライン色
            back_color: 背景色
            bold: 太字 (0 or 1)
            italic: イタリック (0 or 1)
            underline: 下線 (0 or 1)
            strikeout: 取り消し線 (0 or 1)
            scale_x: X軸スケール
            scale_y: Y軸スケール
            spacing: 文字間隔
            angle: 角度
            border_style: 境界線スタイル
            outline: アウトライン幅
            shadow: シャドウ幅
            alignment: 配置 (1-9)
            margin_l: 左マージン
            margin_r: 右マージン
            margin_v: 垂直マージン
            encoding: エンコーディング
        """
        self.styles[name] = {
            'fontname': font_name,
            'fontsize': font_size,
            'primary_color': primary_color,
            'secondary_color': secondary_color,
            'outline_color': outline_color,
            'back_color': back_color,
            'bold': bold,
            'italic': italic,
            'underline': underline,
            'strikeout': strikeout,
            'scale_x': scale_x,
            'scale_y': scale_y,
            'spacing': spacing,
            'angle': angle,
            'border_style': border_style,
            'outline': outline,
            'shadow': shadow,
            'alignment': alignment,
            'margin_l': margin_l,
            'margin_r': margin_r,
            'margin_v': margin_v,
            'encoding': encoding
        }
    
    def add_dialogue(self, start_time: str, end_time: str, style: str, text: str,
                    layer: int = 0, margin_l: int = 0, margin_r: int = 0, margin_v: int = 0,
                    effect: str = ""):
        """ダイアログイベントを追加
        
        Args:
            start_time: 開始時間 (H:MM:SS.CC)
            end_time: 終了時間 (H:MM:SS.CC)
            style: スタイル名
            text: テキスト
            layer: レイヤー
            margin_l: 左マージン
            margin_r: 右マージン
            margin_v: 垂直マージン
            effect: エフェクト
        """
        self.events.append({
            'layer': layer,
            'start': start_time,
            'end': end_time,
            'style': style,
            'name': '',
            'margin_l': margin_l,
            'margin_r': margin_r,
            'margin_v': margin_v,
            'effect': effect,
            'text': text
        })
    
    def build(self) -> str:
        """ASSファイル内容を構築
        
        Returns:
            完全なASS文字列
        """
        ass_content = f"""[Script Info]
Title: {self.title}
ScriptType: v4.00+
WrapStyle: 2
PlayResX: {self.width}
PlayResY: {self.height}
ScaledBorderAndShadow: yes
YCbCr Matrix: TV.709

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
"""
        
        # スタイル追加
        for name, style in self.styles.items():
            style_line = f"Style: {name},{style['fontname']},{style['fontsize']},{style['primary_color']},{style['secondary_color']},{style['outline_color']},{style['back_color']},{style['bold']},{style['italic']},{style['underline']},{style['strikeout']},{style['scale_x']},{style['scale_y']},{style['spacing']},{style['angle']},{style['border_style']},{style['outline']},{style['shadow']},{style['alignment']},{style['margin_l']},{style['margin_r']},{style['margin_v']},{style['encoding']}\n"
            ass_content += style_line
        
        ass_content += "\n[Events]\nFormat: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text\n"
        
        # イベント追加
        for event in self.events:
            event_line = f"Dialogue: {event['layer']},{event['start']},{event['end']},{event['style']},{event['name']},{event['margin_l']},{event['margin_r']},{event['margin_v']},{event['effect']},{event['text']}\n"
            ass_content += event_line
        
        return ass_content
    
    
    def save(self, file_path: str) -> bool:
        """ASSファイルを保存
        
        Args:
            file_path: 保存先ファイルパス
        
        Returns:
            保存成功の可否
        """
        try:
            content = self.build()
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            return True
        except Exception as e:
            print(f"❌ ASSファイル保存エラー: {e}")
            return False


def create_default_style(name: str, font_size: int = 64) -> Dict[str, Any]:
    """デフォルトスタイルを作成
    
    Args:
        name: スタイル名
        font_size: フォントサイズ
        
    Returns:
        スタイル設定辞書
    """
    return {
        'name': name,
        'font_name': 'Arial',
        'font_size': font_size,
        'primary_color': '&H00FFFFFF',
        'secondary_color': '&H000000FF',
        'outline_color': '&H00000000',
        'back_color': '&H80000000',
        'bold': 1,
        'italic': 0,
        'underline': 0,
        'strikeout': 0,
        'scale_x': 100,
        'scale_y': 100,
        'spacing': 0,
        'angle': 0,
        'border_style': 1,
        'outline': 3,
        'shadow': 0,
        'alignment': 5,
        'margin_l': 60,
        'margin_r': 60,
        'margin_v': 60,
        'encoding': 1
    }