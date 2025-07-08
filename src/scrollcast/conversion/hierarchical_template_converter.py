"""
Hierarchical Template-based ASS to HTML converter
階層テンプレート構造対応ASS→HTML変換クラス
"""

import re
import json
import os
from typing import List, Dict, Any
from .utils import ASSTimeUtils, ASSMetadataExtractor, ASSDialogueParser
from .typewriter_fade_plugin_converter import TypewriterFadePluginConverter, CharacterTiming
from .railway_scroll_plugin_converter import RailwayScrollPluginConverter
from .simple_role_plugin_converter import SimpleRolePluginConverter
from .revolver_up_plugin_converter import RevolverUpPluginConverter


class HierarchicalTemplateConverter:
    """階層テンプレート構造を使用するASS→HTML変換クラス"""
    
    def __init__(self, template_name: str):
        self.template_name = template_name
        self.template_mapping = {
            "typewriter_fade": {
                "category": "typewriter",
                "converter_class": TypewriterFadePluginConverter,
                "template_path": "src/templates/typewriter/typewriter_fade"
            },
            "railway_scroll": {
                "category": "railway", 
                "converter_class": RailwayScrollPluginConverter,
                "template_path": "src/templates/railway/railway_scroll"
            },
            "simple_role": {
                "category": "scroll",
                "converter_class": SimpleRolePluginConverter,
                "template_path": "src/templates/scroll/scroll_role"
            },
            "revolver_up": {
                "category": "scroll",
                "converter_class": RevolverUpPluginConverter,
                "template_path": "src/templates/scroll/revolver_up"
            }
        }
        
        if template_name not in self.template_mapping:
            raise ValueError(f"Unsupported template: {template_name}")
            
        self.template_info = self.template_mapping[template_name]
        self.data_converter = self.template_info["converter_class"]()
    
    def convert_ass_to_html(self, ass_file_path: str, html_output_path: str) -> None:
        """ASSファイルを階層テンプレート構造のHTMLに変換"""
        
        # 新しい外部JavaScript参照システムを使用
        self.data_converter.parse_ass_file(ass_file_path)
        self.data_converter.generate_html(html_output_path)
        
        # 統計情報を表示
        timing_data = self._extract_timing_data()
        sentences_count = len(timing_data) if timing_data else 0
        
        print(f"✅ Hierarchical Template HTML generation completed:")
        print(f"   Template: {self.template_name} (Category: {self.template_info['category']})")
        print(f"   Input: {ass_file_path}")
        print(f"   Output: {html_output_path}")
        print(f"   Template Path: {self.template_info['template_path']}")
        print(f"   Lines: {sentences_count}")
        
        # 文字数を計算
        if hasattr(self.data_converter, 'characters') and self.data_converter.characters:
            total_chars = sum(len(char.char) for char in self.data_converter.characters)
            print(f"   Characters: {total_chars}")
    
    def _load_hierarchical_template(self) -> str:
        """階層テンプレート構造からtemplate.htmlを読み込み"""
        template_path = os.path.join(self.template_info["template_path"], "sc-template.html")
        
        if not os.path.exists(template_path):
            raise FileNotFoundError(f"Template file not found: {template_path}")
            
        with open(template_path, 'r', encoding='utf-8') as f:
            return f.read()
    
    def _extract_timing_data(self) -> List[Dict[str, Any]]:
        """タイミングデータを抽出"""
        if self.template_name == "typewriter_fade":
            return self._extract_typewriter_timing_data()
        elif self.template_name == "railway_scroll":
            return self._extract_railway_timing_data()
        elif self.template_name == "simple_role":
            return self._extract_simple_role_timing_data()
        else:
            raise NotImplementedError(f"Timing data extraction for {self.template_name} not implemented")
    
    def _extract_typewriter_timing_data(self) -> List[Dict[str, Any]]:
        """TypewriterFade用タイミングデータを抽出"""
        # 行番号でグループ化
        sentences_dict = {}
        
        for timing in self.data_converter.character_timings:
            line_number = timing.line_number
            if line_number not in sentences_dict:
                sentences_dict[line_number] = []
            sentences_dict[line_number].append(timing)
        
        # 開始時間順にソート
        sorted_sentences = sorted(sentences_dict.items(), key=lambda x: min(t.fade_start_ms for t in x[1]))
        
        # タイミングデータを生成
        timing_data = []
        
        for sequence_index, (line_number, char_timings) in enumerate(sorted_sentences):
            sorted_chars = sorted(char_timings, key=lambda x: x.fade_start_ms)
            
            # 文の開始・終了時間
            sentence_start = min(t.dialogue_start_ms for t in sorted_chars)
            sentence_end = max(t.dialogue_end_ms for t in sorted_chars)
            
            # 文字タイミング
            character_timings = []
            for timing in sorted_chars:
                relative_start = timing.fade_start_ms - sentence_start
                relative_end = timing.fade_end_ms - sentence_start
                character_timings.append({
                    "char": timing.char,
                    "fade_start_ms": relative_start,
                    "fade_end_ms": relative_end
                })
            
            timing_data.append({
                "sequence_index": sequence_index,
                "start_time": sentence_start,
                "end_time": sentence_end,
                "duration": sentence_end - sentence_start,
                "character_timings": character_timings
            })
        
        return timing_data
    
    def _extract_railway_timing_data(self) -> List[Dict[str, Any]]:
        """RailwayScroll用タイミングデータを抽出"""
        timing_data = []
        
        for sequence_index, line_timing in enumerate(self.data_converter.line_timings):
            timing_data.append({
                "sequence_index": sequence_index,
                "text": line_timing.text,
                "fade_in_start": line_timing.fade_in_start_ms,
                "fade_in_end": line_timing.fade_in_end_ms,
                "fade_in_duration": line_timing.fade_in_end_ms - line_timing.fade_in_start_ms,
                "static_start": line_timing.static_start_ms,
                "static_end": line_timing.static_end_ms,
                "static_duration": line_timing.static_end_ms - line_timing.static_start_ms,
                "fade_out_start": line_timing.fade_out_start_ms,
                "fade_out_end": line_timing.fade_out_end_ms,
                "fade_out_duration": line_timing.fade_out_end_ms - line_timing.fade_out_start_ms,
                "start_time": line_timing.fade_in_start_ms,
                "end_time": line_timing.fade_out_end_ms,
                "duration": line_timing.fade_out_end_ms - line_timing.fade_in_start_ms
            })
        
        return timing_data
    
    def _extract_simple_role_timing_data(self) -> List[Dict[str, Any]]:
        """SimpleRole用タイミングデータを抽出"""
        timing_data = []
        
        for sequence_index, line_timing in enumerate(self.data_converter.line_timings):
            timing_data.append({
                "sequence_index": sequence_index,
                "text": line_timing.text,
                "start_time": line_timing.start_ms,
                "end_time": line_timing.end_ms,
                "duration": line_timing.end_ms - line_timing.start_ms
            })
        
        return timing_data
    
    def _generate_sentences_html(self) -> str:
        """文要素のHTMLを生成"""
        if self.template_name == "typewriter_fade":
            return self._generate_typewriter_sentences_html()
        elif self.template_name == "railway_scroll":
            return self._generate_railway_lines_html_from_converter()
        elif self.template_name == "simple_role":
            return self._generate_simple_role_lines_html_from_converter()
        else:
            raise NotImplementedError(f"HTML generation for {self.template_name} not implemented")
    
    def _generate_typewriter_sentences_html(self) -> str:
        """TypewriterFade用の文要素HTMLを生成"""
        # 行番号でグループ化
        sentences_dict = {}
        
        for timing in self.data_converter.character_timings:
            line_number = timing.line_number
            if line_number not in sentences_dict:
                sentences_dict[line_number] = []
            sentences_dict[line_number].append(timing)
        
        # HTMLを生成
        html_parts = []
        sorted_sentences = sorted(sentences_dict.items(), key=lambda x: min(t.fade_start_ms for t in x[1]))
        
        for sequence_index, (line_number, char_timings) in enumerate(sorted_sentences):
            sorted_chars = sorted(char_timings, key=lambda x: x.fade_start_ms)
            
            # 文字要素を生成
            char_elements = []
            for timing in sorted_chars:
                # スペース文字を適切にエスケープ
                char = timing.char
                if char == ' ':
                    char = '&nbsp;'  # ノーブレークスペース
                elif char == '\t':
                    char = '&nbsp;&nbsp;&nbsp;&nbsp;'  # タブを4つのスペースに
                char_elements.append(f'<span class="typewriter-char">{char}</span>')
            
            # 文要素を生成
            sentence_html = f'''        <div class="typewriter-sentence" data-sequence="{sequence_index}">
            {"".join(char_elements)}
        </div>'''
            html_parts.append(sentence_html)
        
        return "\n".join(html_parts)
    
    def _generate_railway_lines_html_from_converter(self) -> str:
        """RailwayScroll用のライン要素HTMLを生成（コンバーターから）"""
        html_parts = []
        
        for sequence_index, line_timing in enumerate(self.data_converter.line_timings):
            line_html = f'        <div class="railway-line" data-sequence="{sequence_index}">{line_timing.text}</div>'
            html_parts.append(line_html)
        
        return "\n".join(html_parts)
    
    def _generate_simple_role_lines_html_from_converter(self) -> str:
        """SimpleRole用のライン要素HTMLを生成（コンバーターから）"""
        html_parts = []
        
        for sequence_index, line_timing in enumerate(self.data_converter.line_timings):
            line_html = f'        <div class="scroll-line" data-sequence="{sequence_index}">{line_timing.text}</div>'
            html_parts.append(line_html)
        
        return "\n".join(html_parts)
    
    def _generate_template_config(self) -> Dict[str, Any]:
        """テンプレート設定を生成（専用コンバーターから取得）"""
        template_config = self.data_converter.get_template_config()
        
        # TemplateConfigをDictに変換
        return {
            "template_name": template_config.template_name,
            "navigation_unit": template_config.navigation_unit,
            "plugin_configs": template_config.plugin_configs
        }
    
    def _inject_data_into_template(self, template_html: str, sentences_html: str, 
                                 timing_data: List[Dict[str, Any]], 
                                 template_config: Dict[str, Any]) -> str:
        """テンプレートにデータを注入"""
        
        # プレースホルダーを置換
        html = template_html
        
        # パスを修正（contents/html/ からの相対パスに変更）
        html = self._fix_relative_paths(html)
        
        # 初期状態制御CSS追加
        html = self._add_initial_state_control(html)
        
        # 文要素HTML
        if self.template_name == "typewriter_fade":
            html = html.replace("{{SENTENCES_HTML}}", sentences_html)
        elif self.template_name in ["railway_scroll", "simple_role"]:
            html = html.replace("{{LINES_HTML}}", sentences_html)
        
        # タイミングデータ
        timing_json = json.dumps(timing_data, ensure_ascii=False, indent=4)
        html = html.replace("{{TIMING_DATA}}", timing_json)
        
        # テンプレート設定
        config_json = json.dumps(template_config, ensure_ascii=False, indent=4)
        html = html.replace("{{TEMPLATE_CONFIG}}", config_json)
        
        return html
    
    def _fix_relative_paths(self, html: str) -> str:
        """contents/html/ からの正しい相対パスに修正"""
        template_info = self.template_info
        
        # 共通アセットパスを修正
        html = html.replace('href="../../../assets/scrollcast-styles.css"', 
                           'href="shared/scrollcast-styles.css"')
        
        if self.template_name == "typewriter_fade":
            # CSS参照を修正
            html = html.replace('href="sc-template.css"', 
                               'href="templates/typewriter/typewriter_fade/sc-template.css"')
            
            # JavaScript参照を修正
            html = html.replace('src="../../../assets/scrollcast-base.js"', 
                               'src="shared/scrollcast-base.js"')
            html = html.replace('src="../sc-base.js"', 
                               'src="templates/typewriter/sc-base.js"')
            html = html.replace('src="sc-template.js"', 
                               'src="templates/typewriter/typewriter_fade/sc-template.js"')
        
        elif self.template_name == "railway_scroll":
            # CSS参照を修正
            html = html.replace('href="sc-template.css"', 
                               'href="templates/railway/railway_scroll/sc-template.css"')
            
            # JavaScript参照を修正
            html = html.replace('src="../../../assets/scrollcast-base.js"', 
                               'src="shared/scrollcast-base.js"')
            html = html.replace('src="../sc-base.js"', 
                               'src="templates/railway/sc-base.js"')
            html = html.replace('src="sc-template.js"', 
                               'src="templates/railway/railway_scroll/sc-template.js"')
        
        elif self.template_name == "simple_role":
            # CSS参照を修正
            html = html.replace('href="sc-template.css"', 
                               'href="templates/scroll/scroll_role/sc-template.css"')
            
            # JavaScript参照を修正
            html = html.replace('src="../../../assets/scrollcast-base.js"', 
                               'src="shared/scrollcast-base.js"')
            html = html.replace('src="../sc-base.js"', 
                               'src="templates/scroll/sc-base.js"')
            html = html.replace('src="sc-template.js"', 
                               'src="templates/scroll/scroll_role/sc-template.js"')
        
        return html
    
    def _add_initial_state_control(self, html: str) -> str:
        """初期状態制御のCSSを追加"""
        if self.template_name == "typewriter_fade":
            initial_control_css = '''
    
    <!-- 初期状態制御 -->
    <style>
        /* 全ての文を最初は非表示にする */
        .typewriter-sentence {
            display: none !important;
        }
        
        /* アクティブな文のみ表示 */
        .typewriter-sentence.active {
            display: block !important;
        }
        
        /* 文字の初期状態 */
        .typewriter-char {
            opacity: 0 !important;
            transform: scale(0.8) !important;
        }
        
        /* 表示された文字 */
        .typewriter-char.visible {
            opacity: 1 !important;
            transform: scale(1) !important;
            transition: opacity 0.1s ease-in-out, transform 0.1s ease-in-out;
        }
    </style>'''
        
        elif self.template_name == "railway_scroll":
            initial_control_css = '''
    
    <!-- 初期状態制御 -->
    <style>
        /* 全てのラインを最初は非表示にする */
        .railway-line {
            display: none !important;
        }
        
        /* アクティブなラインのみ表示 */
        .railway-line.active {
            display: block !important;
        }
        
        /* Railway アニメーション初期状態（!importantを削除してJSアニメーションを有効化） */
        .railway-line {
            opacity: 0;
            transform: translateY(100vh) scale(0.9);
        }
        
        /* Railway アニメーション表示状態（!importantを削除してJSアニメーションを有効化） */
        .railway-line.animating {
            /* JavaScriptアニメーションに委ねるため、静的な値は設定しない */
        }
    </style>'''
        
        elif self.template_name == "simple_role":
            initial_control_css = '''
    
    <!-- 初期状態制御 -->
    <style>
        /* 全てのラインを最初は非表示にする */
        .scroll-line {
            display: none !important;
            opacity: 0;
            transform: translateY(100vh);
        }
        
        /* アクティブなラインのみ表示 */
        .scroll-line.active {
            display: block !important;
        }
        
        /* Scroll アニメーション表示状態（JavaScriptで制御） */
        .scroll-line.active.animating {
            /* JavaScriptアニメーションに委ねるため、静的な値は設定しない */
        }
    </style>'''
        
        else:
            # デフォルトの制御CSS
            initial_control_css = '''
    
    <!-- 初期状態制御 -->
    <style>
        /* 基本的な非表示制御 */
        .template-element {
            display: none !important;
        }
        
        .template-element.active {
            display: block !important;
        }
    </style>'''
        
        # </head>の直前に挿入
        html = html.replace('</head>', initial_control_css + '\n</head>')
        
        return html