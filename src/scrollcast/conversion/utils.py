"""
ASS to HTML conversion utilities
共通ユーティリティ関数
"""

import re
from typing import List, Tuple, NamedTuple
from dataclasses import dataclass
from pathlib import Path


@dataclass
class ASSMetadata:
    """ASSファイルのメタデータ"""
    play_res_x: int = 1080
    play_res_y: int = 1920
    font_size: int = 64
    font_family: str = "Arial"
    total_duration_ms: int = 0
    
    @property
    def responsive_font_size(self) -> float:
        """レスポンシブフォントサイズ（vw単位）を計算"""
        return round(self.font_size * 100 / self.play_res_x, 2)


class ASSTimeUtils:
    """ASS時間形式のユーティリティ"""
    
    @staticmethod
    def to_milliseconds(time_str: str) -> int:
        """ASS時間形式をミリ秒に変換
        
        Args:
            time_str: ASS時間形式 (例: "0:00:01.75")
            
        Returns:
            ミリ秒
        """
        time_parts = time_str.split(':')
        hours = int(time_parts[0])
        minutes = int(time_parts[1])
        seconds_parts = time_parts[2].split('.')
        seconds = int(seconds_parts[0])
        centiseconds = int(seconds_parts[1]) if len(seconds_parts) > 1 else 0
        
        total_ms = (hours * 3600 + minutes * 60 + seconds) * 1000 + centiseconds * 10
        return total_ms


class ASSMetadataExtractor:
    """ASSファイルからメタデータを抽出するユーティリティ"""
    
    @staticmethod
    def extract_resolution(content: str) -> Tuple[int, int]:
        """解像度情報を抽出
        
        Args:
            content: ASSファイルの内容
            
        Returns:
            (width, height) のタプル
        """
        res_x_match = re.search(r'PlayResX:\s*(\d+)', content)
        res_y_match = re.search(r'PlayResY:\s*(\d+)', content)
        
        play_res_x = int(res_x_match.group(1)) if res_x_match else 1080
        play_res_y = int(res_y_match.group(1)) if res_y_match else 1920
        
        return play_res_x, play_res_y
    
    @staticmethod
    def extract_font_info(content: str, target_style_name: str) -> Tuple[str, int]:
        """フォント情報を抽出
        
        Args:
            content: ASSファイルの内容
            target_style_name: 対象スタイル名（部分マッチ）
            
        Returns:
            (font_family, font_size) のタプル
        """
        style_pattern = r'Style:\s*([^,]+),([^,]+),(\d+),'
        style_matches = re.findall(style_pattern, content)
        
        for style_name, font_family, font_size in style_matches:
            if target_style_name in style_name:
                return font_family, int(font_size)
        
        # デフォルト値
        return "Arial", 64
    
    @staticmethod
    def extract_metadata(content: str, target_style_name: str) -> ASSMetadata:
        """ASSファイルから包括的なメタデータを抽出
        
        Args:
            content: ASSファイルの内容
            target_style_name: 対象スタイル名
            
        Returns:
            ASSMetadataオブジェクト
        """
        play_res_x, play_res_y = ASSMetadataExtractor.extract_resolution(content)
        font_family, font_size = ASSMetadataExtractor.extract_font_info(content, target_style_name)
        
        return ASSMetadata(
            play_res_x=play_res_x,
            play_res_y=play_res_y,
            font_size=font_size,
            font_family=font_family
        )


class ASSDialogueParser:
    """ASSファイルのDialogue行を解析するユーティリティ"""
    
    @staticmethod
    def parse_dialogues(content: str) -> List[Tuple[str, str, str, str]]:
        """Dialogue行を抽出
        
        Args:
            content: ASSファイルの内容
            
        Returns:
            (layer, start_time, end_time, text_with_tags) のタプルのリスト
            
        Raises:
            ValueError: Dialogue行が見つからない場合
        """
        dialogue_pattern = r'Dialogue:\s*(\d+),([^,]+),([^,]+),[^,]*,[^,]*,[^,]*,[^,]*,[^,]*,[^,]*,(.+)'
        dialogue_matches = re.findall(dialogue_pattern, content)
        
        if not dialogue_matches:
            raise ValueError("Dialogue行が見つかりません")
        
        return dialogue_matches
    
    @staticmethod
    def calculate_total_duration(dialogue_matches: List[Tuple[str, str, str, str]]) -> int:
        """総再生時間を計算
        
        Args:
            dialogue_matches: parse_dialogues()の戻り値
            
        Returns:
            総再生時間（ミリ秒）
        """
        max_end_time = 0
        for layer, start_time, end_time, text_with_tags in dialogue_matches:
            end_ms = ASSTimeUtils.to_milliseconds(end_time)
            max_end_time = max(max_end_time, end_ms)
        
        return max_end_time


class HTMLTemplateBuilder:
    """HTML共通テンプレートビルダー"""
    
    @staticmethod
    def build_head(title: str) -> str:
        """HTMLヘッドセクションを構築
        
        Args:
            title: ページタイトル
            
        Returns:
            HTMLヘッドセクション
        """
        return f"""<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>"""
    
    @staticmethod
    def build_base_css_minimal() -> str:
        """最小限の基本CSSスタイルを構築"""
        return """        body {
            font-family: Arial, sans-serif;
            margin: 0;
            padding: 0;
            background: #000;
            color: #fff;
            height: 100vh;
            overflow: hidden;
            user-select: none;
            cursor: pointer;
        }"""
    
    @staticmethod
    def build_base_css(metadata: ASSMetadata) -> str:
        """基本CSSスタイルを構築
        
        Args:
            metadata: ASSメタデータ
            
        Returns:
            基本CSSスタイル
        """
        return f"""        body {{
            font-family: {metadata.font_family}, sans-serif;
            margin: 0;
            padding: 0;
            background: #000;
            color: #fff;
            height: 100vh;
            overflow: hidden;
            user-select: none;
            cursor: pointer;
        }}
        
        .container {{
            position: fixed;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            font-size: {metadata.responsive_font_size}vw;
            font-weight: bold;
            text-align: center;
            width: 90%;
            max-width: 400px;
            line-height: 1.4;
        }}
        
        /* デスクトップ表示での固定サイズ */
        @media (min-width: 768px) {{
            .container {{
                font-size: {metadata.font_size}px;
                max-width: 600px;
            }}
        }}"""
    
    @staticmethod
    def build_ui_elements_css() -> str:
        """UI要素CSSを構築（デバッグ要素なし）"""
        return """        .control-hint {
            position: fixed;
            bottom: 20px;
            left: 50%;
            transform: translateX(-50%);
            background: rgba(255, 255, 255, 0.1);
            padding: 10px 20px;
            border-radius: 20px;
            font-size: 12px;
            opacity: 0.7;
        }"""
    
    @staticmethod
    def build_ui_elements_html(counter_label: str, control_hint_text: str, 
                              current_id: str = "current-item", total_id: str = "total-items") -> str:
        """UI要素HTMLを構築（デバッグ要素を除外したクリーンな表示）
        
        Args:
            counter_label: カウンタラベル（"文" or "行"）
            control_hint_text: 操作ヒントテキスト
            current_id: 現在位置表示用のID
            total_id: 総数表示用のID
            
        Returns:
            UI要素HTML（デバッグ要素なし）
        """
        return f"""    <div class="control-hint">
        {control_hint_text} • タップ/クリックで再生制御
    </div>"""
    
