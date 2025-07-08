"""
CLI Argument Parser
コマンドライン引数解析
"""

import argparse
import sys
from typing import Dict, Any, List, Optional


class CLIArgumentParser:
    """CLI引数解析クラス"""
    
    def __init__(self):
        self.parser = self._create_parser()
    
    def _create_parser(self) -> argparse.ArgumentParser:
        """引数パーサーを作成"""
        parser = argparse.ArgumentParser(
            prog='subtitle-generator',
            description='字幕動画生成ツール - さまざまなエフェクトで字幕動画を簡単作成',
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog="""
使用例:
  # タイプライター・フェード効果
  subtitle-generator typewriter_fade "Hello world"
  
  # 鉄道方向幕風効果
  subtitle-generator railway_scroll "Welcome to Tokyo"
  
  # パラメータ指定
  subtitle-generator typewriter_fade "Hello world" --char-interval 200 --font-size 72
  
  # 出力ファイル指定
  subtitle-generator railway_scroll "Welcome" --output my_video.mp4
  
  # テンプレート一覧表示
  subtitle-generator --list-templates
  
  # テンプレートヘルプ表示
  subtitle-generator typewriter_fade --help-template
            """
        )
        
        # グローバルオプション
        parser.add_argument(
            '--version', 
            action='version', 
            version='subtitle-generator 1.0.0'
        )
        
        parser.add_argument(
            '--list-templates',
            action='store_true',
            help='利用可能なテンプレート一覧を表示'
        )
        
        # メインコマンド
        subparsers = parser.add_subparsers(
            dest='template',
            help='使用するテンプレート',
            metavar='TEMPLATE'
        )
        
        # 各テンプレート用のサブパーサーは動的に追加
        self._add_template_subparsers(subparsers)
        
        return parser
    
    def _add_template_subparsers(self, subparsers):
        """テンプレート用のサブパーサーを追加"""
        # テンプレートエンジンを初期化してテンプレート情報を取得
        try:
            from ..template_engine import TemplateEngine
            engine = TemplateEngine()
            
            for template_name in engine.list_templates():
                template = engine.get_template(template_name)
                if template:
                    self._add_template_parser(subparsers, template_name, template, engine)
        
        except Exception as e:
            print(f"Warning: Failed to load template information: {e}")
    
    def _add_template_parser(self, subparsers, template_name: str, template, engine):
        """単一テンプレート用のパーサーを追加"""
        info = template.template_info
        
        # サブパーサー作成
        parser = subparsers.add_parser(
            template_name,
            help=info.description,
            description=f"{info.name} - {info.description}"
        )
        
        # テキスト引数（必須）
        parser.add_argument(
            'text',
            help='字幕テキスト'
        )
        
        # 共通オプション
        parser.add_argument(
            '--output', '-o',
            default=f'{template_name}_output.html',
            help='出力HTMLファイル名 (デフォルト: %(default)s)'
        )
        
        parser.add_argument(
            '--ass-output',
            help='ASS字幕ファイル出力パス（指定しない場合は一時ファイル）'
        )
        
        parser.add_argument(
            '--resolution',
            default='1080x1920',
            help='動画解像度 (デフォルト: %(default)s)'
        )
        
        parser.add_argument(
            '--font-size',
            type=int,
            default=64,
            help='フォントサイズ (デフォルト: %(default)s)'
        )
        
        parser.add_argument(
            '--preset',
            type=str,
            help='プリセット名（config/template.yamlで定義されたパラメータセット）'
        )
        
        parser.add_argument(
            '--html-only',
            action='store_true',
            help='HTMLファイルのみ生成（ASSファイルを生成しない）'
        )
        
        parser.add_argument(
            '--ass-only',
            action='store_true',
            help='ASSファイルのみ生成（HTMLファイルを生成しない）'
        )
        
        parser.add_argument(
            '--help-template',
            action='store_true',
            help='このテンプレートの詳細ヘルプを表示'
        )
        
        # テンプレート固有のパラメータを追加（共通パラメータを除く）
        common_params = {'font_size', 'resolution'}
        for param_name in template.list_parameters():
            if param_name not in common_params:
                param_info = template.get_parameter_info(param_name)
                if param_info:
                    self._add_parameter_argument(parser, param_info)
    
    def _add_parameter_argument(self, parser, param_info):
        """パラメータ引数を追加"""
        arg_name = f'--{param_info.name.replace("_", "-")}'
        
        kwargs = {
            'type': param_info.type,
            'default': param_info.default,
            'help': f'{param_info.description} (デフォルト: %(default)s)'
        }
        
        # 選択肢がある場合
        if param_info.choices:
            kwargs['choices'] = param_info.choices
        
        # 数値範囲の情報をヘルプに追加
        if param_info.min_value is not None or param_info.max_value is not None:
            range_text = f" [範囲: {param_info.min_value or '∞'}-{param_info.max_value or '∞'}]"
            kwargs['help'] += range_text
        
        parser.add_argument(arg_name, **kwargs)
    
    def parse_args(self, args: Optional[List[str]] = None) -> Dict[str, Any]:
        """引数を解析
        
        Args:
            args: 解析する引数リスト（Noneの場合はsys.argv使用）
        
        Returns:
            解析された引数の辞書
        """
        parsed = self.parser.parse_args(args)
        
        # 特別な処理
        if parsed.list_templates:
            self._show_templates_list()
            sys.exit(0)
        
        if hasattr(parsed, 'help_template') and parsed.help_template:
            self._show_template_help(parsed.template)
            sys.exit(0)
        
        # テンプレートが指定されていない場合
        if not parsed.template:
            self.parser.print_help()
            sys.exit(1)
        
        # 辞書に変換
        result = vars(parsed)
        
        # 解像度を解析
        if 'resolution' in result:
            resolution_str = result['resolution']
            try:
                width, height = map(int, resolution_str.split('x'))
                result['resolution'] = (width, height)
            except ValueError:
                print(f"❌ 無効な解像度形式: {resolution_str}")
                print("正しい形式: WIDTHxHEIGHT (例: 1080x1920)")
                sys.exit(1)
        
        return result
    
    def _show_templates_list(self):
        """テンプレート一覧を表示"""
        try:
            from ..template_engine import TemplateEngine
            engine = TemplateEngine()
            
            templates = engine.list_templates()
            print(f"利用可能なテンプレート ({len(templates)}個):\n")
            
            for template_name in sorted(templates):
                info = engine.get_template_info(template_name)
                if info:
                    print(f"  {template_name:<20} - {info.description}")
            
            print(f"\n使用方法:")
            print(f"  subtitle-generator TEMPLATE_NAME \"テキスト\" [オプション...]")
            print(f"\n詳細ヘルプ:")
            print(f"  subtitle-generator TEMPLATE_NAME --help-template")
            
        except Exception as e:
            print(f"❌ テンプレート一覧の取得に失敗: {e}")
    
    def _show_template_help(self, template_name: str):
        """テンプレートヘルプを表示"""
        try:
            from ..template_engine import TemplateEngine
            engine = TemplateEngine()
            engine.print_template_help(template_name)
            
        except Exception as e:
            print(f"❌ テンプレートヘルプの表示に失敗: {e}")


def create_cli_parser() -> CLIArgumentParser:
    """CLI引数パーサーを作成
    
    Returns:
        CLIArgumentParserインスタンス
    """
    return CLIArgumentParser()