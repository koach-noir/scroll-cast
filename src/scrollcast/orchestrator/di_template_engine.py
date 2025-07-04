"""
Dependency Injection Template Engine
依存性注入パターンを適用したテンプレートエンジン
"""

from typing import Dict, List, Optional, Any, Union
import os
import time

from ..interfaces import (
    TemplateEngineProtocol,
    TemplateProtocol,
    TextFormatterProtocol,
    VideoGeneratorProtocol,
    ASSBuilderProtocol
)
from ..dependency_injection import ServiceContainer, ServiceFactory
from ..models.output_models import GenerationResult, ASSOutput, VideoOutput
from ..monitoring import get_monitor, get_quality_monitor, MetricType


class DITemplateEngine:
    """依存性注入パターンを使用したテンプレートエンジン"""
    
    def __init__(self, container: ServiceContainer):
        """
        Args:
            container: 依存性注入コンテナ
        """
        self.container = container
        self.factory = ServiceFactory(container)
        self._templates: Dict[str, TemplateProtocol] = {}
        
        # テンプレートを初期化
        self._initialize_templates()
    
    def _initialize_templates(self):
        """利用可能なテンプレートを初期化"""
        template_types = ['typewriter_fade', 'railway_scroll']
        
        for template_type in template_types:
            try:
                template = self.factory.create_template(template_type)
                if template:
                    self._templates[template_type] = template
                    print(f"✅ Template '{template_type}' initialized")
            except Exception as e:
                print(f"⚠️ Failed to initialize template '{template_type}': {e}")
    
    def register_template(self, template: TemplateProtocol) -> None:
        """テンプレートを登録
        
        Args:
            template: 登録するテンプレート
        """
        # テンプレート名を取得（テンプレート固有の方法）
        template_name = getattr(template, 'template_name', 'unknown')
        if hasattr(template, 'template_info'):
            template_name = template.template_info.name
        
        self._templates[template_name] = template
    
    def get_template(self, name: str) -> Optional[TemplateProtocol]:
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
    
    def generate_subtitle(
        self,
        template_name: str,
        text: Union[str, List[str]],
        output_path: str,
        resolution: tuple = (1080, 1920),
        **parameters: Any
    ) -> bool:
        """字幕ASSファイルを生成
        
        Args:
            template_name: テンプレート名
            text: 入力テキスト
            output_path: 出力ASSファイルパス
            resolution: 解像度 (width, height)
            **parameters: テンプレート固有のパラメータ
        
        Returns:
            生成成功の可否
        """
        try:
            template = self.get_template(template_name)
            if not template:
                print(f"❌ Template '{template_name}' not found")
                return False
            
            # テキストフォーマッターを依存性注入で取得
            text_formatter = self.factory.create_text_formatter()
            
            # テキストを処理
            if isinstance(text, str):
                formatted_text = text_formatter.format_for_display(text)
            else:
                # リストの場合は結合してから処理
                combined_text = '\n'.join(text)
                formatted_text = text_formatter.format_for_display(combined_text)
            
            # パラメータをバリデーション
            validated_params = template.validate_parameters(**parameters)
            
            # ASS生成
            ass_content = template.generate_ass_from_formatted(
                formatted_text, 
                resolution=resolution,
                **validated_params
            )
            
            # ファイル保存
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(ass_content)
            
            print(f"✅ ASS subtitle generated: {output_path}")
            return True
            
        except Exception as e:
            print(f"❌ Subtitle generation error: {e}")
            return False
    
    def generate_video(
        self,
        template_name: str,
        text: Union[str, List[str]],
        output_path: str,
        ass_path: Optional[str] = None,
        resolution: tuple = (1080, 1920),
        **parameters: Any
    ) -> bool:
        """動画ファイルを生成
        
        Args:
            template_name: テンプレート名
            text: 入力テキスト
            output_path: 出力動画ファイルパス
            ass_path: ASSファイルパス（Noneの場合は一時ファイル生成）
            resolution: 解像度
            **parameters: テンプレート固有のパラメータ
        
        Returns:
            生成成功の可否
        """
        try:
            # 一時ASSファイルパスを生成
            if ass_path is None:
                base_name = os.path.splitext(output_path)[0]
                ass_path = f"{base_name}.ass"
            
            # ASS字幕を生成
            if not self.generate_subtitle(template_name, text, ass_path, resolution, **parameters):
                return False
            
            # テンプレート取得と時間計算
            template = self.get_template(template_name)
            if not template:
                return False
            
            # テキスト処理
            text_formatter = self.factory.create_text_formatter()
            if isinstance(text, str):
                formatted_text = text_formatter.format_for_display(text)
            else:
                combined_text = '\n'.join(text)
                formatted_text = text_formatter.format_for_display(combined_text)
            
            validated_params = template.validate_parameters(**parameters)
            duration = template.calculate_total_duration(formatted_text, **validated_params)
            
            # 動画ジェネレーターを依存性注入で取得
            video_generator = self.factory.create_video_generator(resolution)
            
            success = video_generator.create_video_with_subtitles(
                ass_file_path=ass_path,
                output_path=output_path,
                duration=duration + 2.0,  # 2秒余裕
                resolution=resolution
            )
            
            if success:
                print(f"✅ Video generated: {output_path}")
            
            return success
            
        except Exception as e:
            print(f"❌ Video generation error: {e}")
            return False
    
    def generate_complete_workflow(
        self,
        template_name: str,
        input_text: str,
        output_dir: str,
        resolution: tuple = (1080, 1920),
        generate_video: bool = True,
        **parameters: Any
    ) -> GenerationResult:
        """完全なワークフローを実行
        
        Args:
            template_name: テンプレート名
            input_text: 入力テキスト
            output_dir: 出力ディレクトリ
            resolution: 解像度
            generate_video: 動画生成フラグ
            **parameters: テンプレート固有のパラメータ
        
        Returns:
            生成結果
        """
        # メトリクス監視開始
        monitor = get_monitor()
        quality_monitor = get_quality_monitor()
        start_time = time.time()
        
        # ワークフロー開始メトリクス
        monitor.record_metric(
            'workflow_started', 1.0, MetricType.BUSINESS,
            {'template_name': template_name, 'resolution': f"{resolution[0]}x{resolution[1]}"}
        )
        
        try:
            # 出力ディレクトリ作成
            os.makedirs(output_dir, exist_ok=True)
            
            # テンプレート取得
            template = self.get_template(template_name)
            if not template:
                raise ValueError(f"Template '{template_name}' not found")
            
            # テキスト処理
            text_formatter = self.factory.create_text_formatter()
            formatted_text = text_formatter.format_for_display(input_text)
            
            # パラメータ設定
            validated_params = template.validate_parameters(**parameters)
            
            # ASS生成
            ass_content = template.generate_ass_from_formatted(
                formatted_text, 
                resolution=resolution,
                **validated_params
            )
            
            # ASS保存
            ass_path = os.path.join(output_dir, f"{template_name}_output.ass")
            with open(ass_path, 'w', encoding='utf-8') as f:
                f.write(ass_content)
            
            # メタデータを作成
            from ..models.output_models import ASSMetadata
            metadata = ASSMetadata()
            metadata.line_count = len(ass_content.split('\n'))
            metadata.character_count = len(ass_content)
            
            ass_output = ASSOutput(
                content=ass_content,
                metadata=metadata
            )
            
            # 動画生成
            video_output = None
            total_duration = template.calculate_total_duration(formatted_text, **validated_params)
            
            if generate_video:
                video_generator = self.factory.create_video_generator(resolution)
                video_path = os.path.join(output_dir, f"{template_name}_output.mp4")
                
                success = video_generator.create_greenscreen_video(
                    ass_file_path=ass_path,
                    output_path=video_path,
                    duration=total_duration,
                    resolution=resolution
                )
                
                if success and os.path.exists(video_path):
                    video_output = VideoOutput(
                        file_path=video_path,
                        resolution=resolution,
                        duration=total_duration
                    )
            
            processing_time = time.time() - start_time
            
            # 成功メトリクス記録
            monitor.record_metric(
                'workflow_completed', 1.0, MetricType.BUSINESS,
                {'template_name': template_name, 'processing_time': processing_time}
            )
            monitor.record_metric(
                'workflow_processing_time', processing_time * 1000, MetricType.PERFORMANCE,
                {'template_name': template_name}
            )
            
            result = GenerationResult(
                success=True,
                ass_output=ass_output,
                video_output=video_output,
                template_name=template_name
            )
            
            # 品質監視に結果を記録
            quality_monitor.record_generation_result(result)
            
            print(f"✅ Complete workflow finished in {processing_time:.2f}s")
            return result
            
        except Exception as e:
            processing_time = time.time() - start_time
            error_message = f"Workflow failed: {str(e)}"
            
            # エラーメトリクス記録
            monitor.record_metric(
                'workflow_failed', 1.0, MetricType.BUSINESS,
                {'template_name': template_name, 'error': str(e), 'processing_time': processing_time}
            )
            
            result = GenerationResult(
                success=False,
                ass_output=None,
                video_output=None,
                template_name=template_name
            )
            result.add_error("workflow_error", error_message)
            
            # 品質監視にエラー結果を記録
            quality_monitor.record_generation_result(result)
            
            print(f"❌ {error_message}")
            return result
    
    def get_template_info(self, template_name: str) -> Optional[Dict[str, Any]]:
        """テンプレート情報を取得
        
        Args:
            template_name: テンプレート名
        
        Returns:
            テンプレート情報辞書またはNone
        """
        template = self.get_template(template_name)
        if not template:
            return None
        
        info = {
            'name': template_name,
            'parameters': template.get_default_parameters()
        }
        
        # テンプレート固有の情報があれば追加
        if hasattr(template, 'template_info'):
            info.update({
                'description': template.template_info.description,
                'version': getattr(template.template_info, 'version', '1.0'),
                'author': getattr(template.template_info, 'author', 'Unknown')
            })
        
        return info
    
    def print_template_help(self, template_name: str):
        """テンプレートのヘルプを表示
        
        Args:
            template_name: テンプレート名
        """
        info = self.get_template_info(template_name)
        if not info:
            print(f"❌ Template '{template_name}' not found")
            return
        
        print(f"\n📝 Template: {info['name']}")
        if 'description' in info:
            print(f"Description: {info['description']}")
        
        parameters = info.get('parameters', {})
        if parameters:
            print(f"\nAvailable parameters:")
            for param_name, default_value in parameters.items():
                print(f"  --{param_name.replace('_', '-')}: {type(default_value).__name__} = {default_value}")
        else:
            print("\nNo parameters available")
    
    def print_all_templates_help(self):
        """全テンプレートのヘルプを表示"""
        templates = self.list_templates()
        print(f"Available templates ({len(templates)}):\n")
        
        for template_name in sorted(templates):
            self.print_template_help(template_name)
            print("-" * 50)