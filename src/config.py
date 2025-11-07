"""
C言語単体テスト自動生成ツール - 設定管理

設定ファイルの読み込み・管理を行う
"""

import json
from pathlib import Path
from typing import Dict, Any, Optional
from dataclasses import dataclass, asdict


@dataclass
class GeneratorConfig:
    """生成器の設定"""
    # 出力設定
    output_dir: str = "output"
    truth_table_suffix: str = "_truth_table.xlsx"
    test_code_prefix: str = "test_"
    io_table_suffix: str = "_io_table.xlsx"
    
    # パーサー設定
    include_paths: list = None
    define_macros: Dict[str, str] = None
    
    # テストコード生成設定
    test_framework: str = "Unity"
    include_mock_stubs: bool = True
    include_comments: bool = True
    
    # Excel出力設定
    excel_format: str = "xlsx"
    include_header_color: bool = True
    
    def __post_init__(self):
        """初期化後処理"""
        if self.include_paths is None:
            self.include_paths = []
        if self.define_macros is None:
            self.define_macros = {}
    
    def to_dict(self) -> Dict[str, Any]:
        """辞書形式に変換"""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'GeneratorConfig':
        """辞書から生成"""
        return cls(**data)


class ConfigManager:
    """設定管理クラス"""
    
    DEFAULT_CONFIG_NAME = "generator_config.json"
    
    def __init__(self, config_path: Optional[str] = None):
        """
        初期化
        
        Args:
            config_path: 設定ファイルのパス（省略時はデフォルト）
        """
        self.config_path = Path(config_path) if config_path else None
        self.config = GeneratorConfig()
    
    def load(self, config_path: Optional[str] = None) -> GeneratorConfig:
        """
        設定ファイルを読み込む
        
        Args:
            config_path: 設定ファイルのパス
        
        Returns:
            GeneratorConfig: 設定オブジェクト
        """
        path = Path(config_path) if config_path else self.config_path
        
        if path and path.exists():
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                self.config = GeneratorConfig.from_dict(data)
                print(f"✅ 設定ファイルを読み込みました: {path}")
            except Exception as e:
                print(f"⚠️ 設定ファイルの読み込みに失敗しました: {e}")
                print(f"   デフォルト設定を使用します")
        else:
            print(f"ℹ️ 設定ファイルが見つかりません。デフォルト設定を使用します")
        
        return self.config
    
    def save(self, config_path: Optional[str] = None) -> bool:
        """
        設定ファイルを保存
        
        Args:
            config_path: 保存先パス
        
        Returns:
            bool: 成功したかどうか
        """
        path = Path(config_path) if config_path else self.config_path
        
        if not path:
            path = Path(self.DEFAULT_CONFIG_NAME)
        
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(self.config.to_dict(), f, indent=2, ensure_ascii=False)
            print(f"✅ 設定ファイルを保存しました: {path}")
            return True
        except Exception as e:
            print(f"❌ 設定ファイルの保存に失敗しました: {e}")
            return False
    
    def get_config(self) -> GeneratorConfig:
        """現在の設定を取得"""
        return self.config
    
    def update_config(self, **kwargs) -> None:
        """
        設定を更新
        
        Args:
            **kwargs: 更新する設定項目
        """
        for key, value in kwargs.items():
            if hasattr(self.config, key):
                setattr(self.config, key, value)
            else:
                print(f"⚠️ 未知の設定項目: {key}")
    
    @staticmethod
    def create_default_config(output_path: str = "generator_config.json") -> bool:
        """
        デフォルト設定ファイルを作成
        
        Args:
            output_path: 出力先パス
        
        Returns:
            bool: 成功したかどうか
        """
        config = GeneratorConfig()
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(config.to_dict(), f, indent=2, ensure_ascii=False)
            print(f"✅ デフォルト設定ファイルを作成しました: {output_path}")
            return True
        except Exception as e:
            print(f"❌ 設定ファイルの作成に失敗しました: {e}")
            return False


# 使用例
if __name__ == "__main__":
    # デフォルト設定ファイルの作成
    ConfigManager.create_default_config()
    
    # 設定の読み込み
    manager = ConfigManager("generator_config.json")
    config = manager.load()
    
    # 設定の表示
    print("\n現在の設定:")
    print(json.dumps(config.to_dict(), indent=2, ensure_ascii=False))
    
    # 設定の更新
    manager.update_config(output_dir="custom_output", include_comments=False)
    
    # 設定の保存
    manager.save("custom_config.json")
