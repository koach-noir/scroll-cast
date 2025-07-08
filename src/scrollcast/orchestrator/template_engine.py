"""
Template Engine
字幕テンプレートエンジン
"""

import os
import importlib
from typing import Dict, List, Optional, Any, Union
from ..coloring.base import BaseTemplate, SubtitleTemplate


class TemplateEngine:
    """字幕テンプレートエンジン"""
    
    def __init__(self):
        self._templates: Dict[str, BaseTemplate] = {}
        self._config_loader = None
        self._discover_templates()
        
    def _get_config_loader(self):
        """Config Loaderのレイジー初期化"""
        if self._config_loader is None:
            from ..config.config_loader import ConfigLoader
            self._config_loader = ConfigLoader()
        return self._config_loader
    
    def _discover_templates(self):
        """利用可能なテンプレートを自動発見"""
        # 手動でテンプレートを登録（自動発見は複雑になるため）
        self._register_builtin_templates()
    
    def _register_builtin_templates(self):
        """組み込みテンプレートを登録"""
        try:
            from ..coloring.typewriter_fade import TypewriterFadeTemplate
            self.register_template(TypewriterFadeTemplate())
        except ImportError as e:
            print(f"Warning: Failed to import TypewriterFadeTemplate: {e}")
        
        try:
            from ..coloring.typewriter_fade_paragraph import TypewriterFadeParagraphTemplate
            self.register_template(TypewriterFadeParagraphTemplate())
        except ImportError as e:
            print(f"Warning: Failed to import TypewriterFadeParagraphTemplate: {e}")
        
        try:
            from ..coloring.railway_scroll import RailwayScrollTemplate
            self.register_template(RailwayScrollTemplate())
        except ImportError as e:
            print(f"Warning: Failed to import RailwayScrollTemplate: {e}")
        
        try:
            from ..coloring.railway_scroll_paragraph import RailwayScrollParagraphTemplate
            self.register_template(RailwayScrollParagraphTemplate())
        except ImportError as e:
            print(f"Warning: Failed to import RailwayScrollParagraphTemplate: {e}")
        
        try:
            from ..coloring.simple_role import SimpleRoleTemplate
            self.register_template(SimpleRoleTemplate())
        except ImportError as e:
            print(f"Warning: Failed to import SimpleRoleTemplate: {e}")
    
    def register_template(self, template: BaseTemplate):
        """テンプレートを登録
        
        Args:
            template: 登録するテンプレート
        """
        template_name = template.template_info.name
        self._templates[template_name] = template
    
    def get_template(self, name: str) -> Optional[BaseTemplate]:
        """テンプレートを取得
        
        Args:
            name: テンプレート名
        
        Returns:
            テンプレートインスタンスまたはNone
        """
        return self._templates.get(name)
    
    def list_templates(self) -> List[str]:
        """利用可能なテンプレート一覧を取得
        
        Returns:
            テンプレート名のリスト
        """
        return list(self._templates.keys())
    
    def get_template_info(self, name: str) -> Optional[SubtitleTemplate]:
        """テンプレート情報を取得
        
        Args:
            name: テンプレート名
        
        Returns:
            テンプレート情報またはNone
        """
        template = self.get_template(name)
        return template.template_info if template else None
    
    def get_template_parameters(self, name: str) -> Optional[List[str]]:
        """テンプレートのパラメータ一覧を取得
        
        Args:
            name: テンプレート名
        
        Returns:
            パラメータ名のリストまたはNone
        """
        template = self.get_template(name)
        return template.list_parameters() if template else None
    
    def generate_subtitle(self, template_name: str, text: Union[str, List[str]], 
                         output_path: str, resolution: tuple = (1080, 1920), preset: Optional[str] = None, **parameters) -> bool:
        """字幕を生成
        
        Args:
            template_name: テンプレート名
            text: 入力テキスト
            output_path: 出力ASSファイルパス
            resolution: 解像度 (width, height)
            preset: プリセット名（指定するとconfig/template_name.yamlからパラメータを読み込み）
            **parameters: テンプレート固有のパラメータ（presetより優先）
        
        Returns:
            生成成功の可否
        """
        template = self.get_template(template_name)
        if not template:
            print(f"❌ テンプレート '{template_name}' が見つかりません")
            return False
        
        try:
            # プリセットがある場合、設定ファイルからパラメータを読み込み
            final_parameters = parameters.copy()
            if preset:
                config_loader = self._get_config_loader()
                template_config = config_loader.load_template_config(template_name)
                if template_config:
                    preset_params = template_config.get_preset_parameters(preset)
                    if preset_params:
                        print(f"✅ プリセット '{preset}' を適用:")
                        for key, value in preset_params.items():
                            print(f"   {key}: {value}")
                        # プリセットパラメータをベースにして、個別パラメータで上書き
                        final_parameters = {**preset_params, **parameters}
                        if parameters:
                            print(f"🔧 個別パラメータで上書き: {list(parameters.keys())}")
                    else:
                        print(f"⚠️  プリセット '{preset}' が見つかりません（テンプレート: {template_name}）")
                        print(f"   利用可能なプリセット: {template_config.get_all_preset_names()}")
                else:
                    print(f"⚠️  設定ファイルが見つかりません: config/{template_name}.yaml")
            
            # パラメータをバリデーション
            validated_params = template.validate_parameters(**final_parameters)
            
            # テキストを処理（font_sizeとresolutionを渡す）
            if isinstance(text, str):
                processed_text = template.process_text(
                    text, 
                    font_size=validated_params.get('font_size', 64),
                    resolution=resolution
                )
            else:
                processed_text = text
            
            # font_sizeとresolutionを含む全パラメータを渡す
            template_specific_params = validated_params.copy()
            
            # ASS効果を生成
            ass_effects = template.generate_ass_effects(processed_text, **template_specific_params)
            
            # 新しいテンプレートは既に完全なASSファイルを生成する
            if template_name in ["railway_scroll", "typewriter_fade", "railway_scroll_paragraph", "typewriter_fade_paragraph"]:
                ass_content = ass_effects
            else:
                # 将来の他のテンプレート用にヘッダーを追加する処理を残す
                from ..packing.ass_builder import ASSBuilder
                builder = ASSBuilder(title=f"{template_name.title()} Effect")
                
                # デフォルトスタイルを追加
                style_name = template_name.replace('_', '').title()
                builder.add_style(style_name, font_size=validated_params.get('font_size', 64))
                
                # 通常のテンプレート処理
                if '\n' in ass_effects:
                    # 複数のDialogue行
                    for line in ass_effects.split('\n'):
                        if line.startswith('Dialogue:'):
                            parts = line.split(',', 9)
                            if len(parts) >= 10:
                                builder.add_dialogue(
                                    start_time=parts[1],
                                    end_time=parts[2],
                                    style=parts[3],
                                    text=parts[9]
                                )
                else:
                    # 単一効果
                    duration = template.calculate_duration(processed_text, **template_specific_params)
                    builder.add_dialogue(
                        start_time="0:00:00.00",
                        end_time=f"0:00:{duration:05.2f}",
                        style=style_name,
                        text=ass_effects
                    )
                
                ass_content = builder.build()
            
            # ファイル保存
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(ass_content)
            
            print(f"✅ ASS字幕ファイル生成完了: {output_path}")
            return True
            
        except Exception as e:
            print(f"❌ 字幕生成エラー: {e}")
            return False
    
    def generate_video(self, template_name: str, text: Union[str, List[str]], 
                      output_path: str, ass_path: Optional[str] = None,
                      resolution: tuple = (1080, 1920), preset: Optional[str] = None, **parameters) -> bool:
        """動画を生成
        
        Args:
            template_name: テンプレート名
            text: 入力テキスト
            output_path: 出力動画ファイルパス
            ass_path: ASSファイルパス（None の場合は一時ファイル生成）
            resolution: 解像度
            preset: プリセット名（指定するとconfig/template_name.yamlからパラメータを読み込み）
            **parameters: テンプレート固有のパラメータ（presetより優先）
        
        Returns:
            生成成功の可否
        """
        # 一時ASSファイルパスを生成
        if ass_path is None:
            base_name = os.path.splitext(output_path)[0]
            ass_path = f"{base_name}.ass"
        
        # resolutionパラメータを分離して渡す
        params_without_resolution = {k: v for k, v in parameters.items() if k != 'resolution'}
        
        # ASS字幕を生成
        if not self.generate_subtitle(template_name, text, ass_path, resolution, preset, **params_without_resolution):
            return False
        
        # 動画時間を計算
        template = self.get_template(template_name)
        if not template:
            return False
        
        validated_params = template.validate_parameters(**parameters)
        
        # テキストを処理（font_sizeとresolutionを渡す）
        if isinstance(text, str):
            processed_text = template.process_text(
                text, 
                font_size=validated_params.get('font_size', 64),
                resolution=resolution
            )
        else:
            processed_text = text
        
        # font_sizeとresolutionを含む全パラメータを渡す
        template_specific_params = validated_params.copy()
        
        duration = template.calculate_duration(processed_text, **template_specific_params)
        
        # 動画生成
        from ..rendering.video_generator import VideoGenerator
        video_gen = VideoGenerator(default_resolution=resolution)
        
        success = video_gen.create_video_with_subtitles(
            ass_file_path=ass_path,
            output_path=output_path,
            duration=duration + 2.0  # 2秒余裕
        )
        
        return success
    
    def print_template_help(self, template_name: str):
        """テンプレートのヘルプを表示
        
        Args:
            template_name: テンプレート名
        """
        template = self.get_template(template_name)
        if not template:
            print(f"❌ テンプレート '{template_name}' が見つかりません")
            return
        
        info = template.template_info
        print(f"\n📝 テンプレート: {info.name}")
        print(f"説明: {info.description}")
        
        parameters = template.list_parameters()
        if parameters:
            print(f"\n利用可能なパラメータ:")
            for param_name in parameters:
                param_info = template.get_parameter_info(param_name)
                if param_info:
                    print(f"  --{param_name.replace('_', '-')}: {param_info.description}")
                    print(f"    型: {param_info.type.__name__}, デフォルト: {param_info.default}")
                    if param_info.min_value is not None or param_info.max_value is not None:
                        range_info = f"範囲: {param_info.min_value or '∞'} - {param_info.max_value or '∞'}"
                        print(f"    {range_info}")
        else:
            print("\nパラメータ: なし")
    
    def print_all_templates_help(self):
        """全テンプレートのヘルプを表示"""
        templates = self.list_templates()
        print(f"利用可能なテンプレート ({len(templates)}個):\n")
        
        for template_name in sorted(templates):
            self.print_template_help(template_name)
            print("-" * 50)