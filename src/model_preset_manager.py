#!/usr/bin/env python3
"""
モデルプリセット管理モジュール

モデル別のマクロ定義プリセットを管理
"""

import json
from pathlib import Path
from typing import Dict, Optional


class ModelPresetManager:
    """モデルプリセット管理クラス"""
    
    def __init__(self, preset_file: Optional[str] = None):
        """
        初期化
        
        Args:
            preset_file: プリセットファイルのパス（省略時はデフォルト）
        """
        self.preset_file = preset_file or "model_presets.json"
        self.presets: Dict[str, Dict] = {}
        self.load_presets()
    
    def load_presets(self) -> bool:
        """
        プリセットファイルを読み込み
        
        Returns:
            成功したかどうか
        """
        preset_path = Path(self.preset_file)
        
        if not preset_path.exists():
            print(f"⚠️ プリセットファイルが見つかりません: {self.preset_file}")
            print(f"   デフォルトのプリセットファイルを作成します")
            self.create_default_preset_file()
            # 作成後に再読み込み
            preset_path = Path(self.preset_file)
        
        try:
            with open(preset_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.presets = data.get('presets', {})
            return True
        except Exception as e:
            print(f"❌ プリセットファイルの読み込みに失敗: {e}")
            return False
    
    def get_preset(self, preset_name: str) -> Optional[Dict[str, str]]:
        """
        指定されたプリセットのマクロ定義を取得
        
        Args:
            preset_name: プリセット名
        
        Returns:
            マクロ定義辞書、またはNone
        """
        if preset_name not in self.presets:
            print(f"❌ プリセットが見つかりません: {preset_name}")
            print(f"   利用可能なプリセット: {', '.join(self.presets.keys())}")
            return None
        
        preset = self.presets[preset_name]
        return preset.get('defines', {})
    
    def list_presets(self) -> None:
        """利用可能なプリセット一覧を表示"""
        if not self.presets:
            print("利用可能なプリセットがありません")
            return
        
        print("=" * 70)
        print("利用可能なモデルプリセット")
        print("=" * 70)
        
        for name, preset in self.presets.items():
            description = preset.get('description', '説明なし')
            defines = preset.get('defines', {})
            
            print(f"\n📋 {name}")
            print(f"   説明: {description}")
            print(f"   定義されるマクロ:")
            for macro_name, macro_value in defines.items():
                print(f"     - {macro_name} = {macro_value}")
        
        print("\n" + "=" * 70)
        print("使用例:")
        print(f"  python main.py -i test.c -f func --preset model_a -o output")
        print("=" * 70)
    
    def create_default_preset_file(self) -> None:
        """デフォルトのプリセットファイルを作成"""
        default_presets = {
            "presets": {
                "model_a": {
                    "description": "Aモデル用の設定",
                    "defines": {
                        "MODEL_A": "1",
                        "TYPE1": "1",
                        "TYPE2": "1",
                        "MAX_SENSORS": "10",
                        "ENABLE_DEBUG": "1"
                    }
                },
                "model_b": {
                    "description": "Bモデル用の設定",
                    "defines": {
                        "MODEL_B": "1",
                        "TYPE1": "1",
                        "TYPE3": "1",
                        "MAX_SENSORS": "8",
                        "ENABLE_LOGGING": "1"
                    }
                },
                "model_c": {
                    "description": "Cモデル用の設定",
                    "defines": {
                        "MODEL_C": "1",
                        "TYPE2": "1",
                        "TYPE3": "1",
                        "DEBUG_MODE": "1",
                        "MAX_BUFFER_SIZE": "256"
                    }
                },
                "production": {
                    "description": "本番環境用の設定",
                    "defines": {
                        "PRODUCTION": "1",
                        "NDEBUG": "1",
                        "OPTIMIZE_LEVEL": "3"
                    }
                }
            }
        }
        
        try:
            with open(self.preset_file, 'w', encoding='utf-8') as f:
                json.dump(default_presets, f, indent=2, ensure_ascii=False)
            print(f"✅ デフォルトのプリセットファイルを作成しました: {self.preset_file}")
        except Exception as e:
            print(f"❌ プリセットファイルの作成に失敗: {e}")


if __name__ == "__main__":
    # テスト実行
    import sys
    
    manager = ModelPresetManager()
    
    if len(sys.argv) > 1 and sys.argv[1] == "list":
        manager.list_presets()
    else:
        # model_aのプリセットを取得
        defines = manager.get_preset("model_a")
        if defines:
            print("\nmodel_aのマクロ定義:")
            for name, value in defines.items():
                print(f"  {name} = {value}")
