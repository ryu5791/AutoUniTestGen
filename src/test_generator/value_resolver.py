"""
ValueResolver モジュール (v3.3.0)

enum定数、マクロ、数値の異なる値を解決するヘルパークラス
変数初期化時のTODOコメント解消に使用
"""

import sys
import os
import re
from typing import Optional, Dict, List, Any, Tuple

# パスを追加
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))
from src.utils import setup_logger


class ValueResolver:
    """
    値解決クラス (v4.3.0 更新)
    
    enum定数、マクロ定数、数値について「異なる値」を自動解決する
    v4.3.0: 型別フォールバック値に対応
    """
    
    # フォールバック値（明らかに異なることを示す値）
    FALLBACK_VALUE = "0xDEADBEEF"
    FALLBACK_VALUE_SHORT = "0xDEAD"
    
    # v4.3.0: 型別フォールバック値テーブル
    FALLBACK_VALUES_BY_TYPE = {
        # 8ビット型
        'uint8_t': '0xDE',
        'int8_t': '0x7E',
        'char': '0x41',           # 'A'
        'unsigned char': '0xDE',
        'signed char': '0x7E',
        # 16ビット型
        'uint16_t': '0xDEAD',
        'int16_t': '0x7EAD',
        'short': '0x7EAD',
        'unsigned short': '0xDEAD',
        # 32ビット型
        'uint32_t': '0xDEADBEEF',
        'int32_t': '0x7EADBEEF',
        'int': '0x7EADBEEF',
        'unsigned int': '0xDEADBEEF',
        'long': '0x7EADBEEF',
        'unsigned long': '0xDEADBEEF',
        # 64ビット型
        'uint64_t': '0xDEADBEEFCAFEBABE',
        'int64_t': '0x7EADBEEFCAFEBABE',
        'long long': '0x7EADBEEFCAFEBABE',
        'unsigned long long': '0xDEADBEEFCAFEBABE',
        # ブール型
        'bool': '1',
        '_Bool': '1',
        # 浮動小数点型
        'float': '3.14f',
        'double': '3.14159',
    }
    
    def __init__(self, parsed_data=None):
        """
        初期化
        
        Args:
            parsed_data: ParsedDataオブジェクト（enum/マクロ情報を含む）
        """
        self.logger = setup_logger(__name__)
        self.parsed_data = parsed_data
        
        # キャッシュ（パフォーマンス向上用）
        self._enum_constant_to_type: Dict[str, str] = {}
        self._build_enum_cache()
    
    def _build_enum_cache(self) -> None:
        """enum定数 -> 型名のキャッシュを構築"""
        if not self.parsed_data:
            return
        
        # enums辞書から構築
        if hasattr(self.parsed_data, 'enums') and self.parsed_data.enums:
            for enum_type, constants in self.parsed_data.enums.items():
                for const in constants:
                    self._enum_constant_to_type[const] = enum_type
    
    def is_numeric(self, value: str) -> bool:
        """
        値が数値かどうかを判定
        
        Args:
            value: 判定対象の値
        
        Returns:
            数値の場合True
        
        Examples:
            >>> resolver.is_numeric("123")
            True
            >>> resolver.is_numeric("0xFF")
            True
            >>> resolver.is_numeric("-42")
            True
            >>> resolver.is_numeric("ENUM_VALUE")
            False
        """
        if not value:
            return False
        
        value = value.strip()
        
        # 16進数
        if value.lower().startswith('0x'):
            try:
                int(value, 16)
                return True
            except ValueError:
                return False
        
        # 8進数
        if value.startswith('0') and len(value) > 1 and value[1:].isdigit():
            try:
                int(value, 8)
                return True
            except ValueError:
                pass
        
        # 10進数（負の数も含む）
        try:
            int(value)
            return True
        except ValueError:
            pass
        
        # 浮動小数点
        try:
            float(value)
            return True
        except ValueError:
            return False
    
    def parse_numeric(self, value: str) -> Optional[int]:
        """
        数値文字列を整数に変換
        
        Args:
            value: 数値文字列
        
        Returns:
            整数値、変換失敗時はNone
        """
        if not value:
            return None
        
        value = value.strip()
        
        # サフィックス（U, L, UL, ULL等）を除去
        value = re.sub(r'[uUlL]+$', '', value)
        
        try:
            # 16進数
            if value.lower().startswith('0x'):
                return int(value, 16)
            
            # 8進数
            if value.startswith('0') and len(value) > 1:
                try:
                    return int(value, 8)
                except ValueError:
                    pass
            
            # 10進数
            return int(value)
        except ValueError:
            return None
    
    def is_enum_constant(self, value: str) -> bool:
        """
        値がenum定数かどうかを判定
        
        Args:
            value: 判定対象の値
        
        Returns:
            enum定数の場合True
        """
        if not value or not self.parsed_data:
            return False
        
        value = value.strip()
        
        # キャッシュから検索
        if value in self._enum_constant_to_type:
            return True
        
        # enum_valuesリストから検索
        if hasattr(self.parsed_data, 'enum_values') and self.parsed_data.enum_values:
            if value in self.parsed_data.enum_values:
                return True
        
        return False
    
    def is_macro_constant(self, value: str) -> bool:
        """
        値がマクロ定数かどうかを判定
        
        Args:
            value: 判定対象の値
        
        Returns:
            マクロ定数の場合True
        """
        if not value or not self.parsed_data:
            return False
        
        value = value.strip()
        
        # macros辞書から検索
        if hasattr(self.parsed_data, 'macros') and self.parsed_data.macros:
            if value in self.parsed_data.macros:
                return True
        
        return False
    
    def get_enum_type(self, constant: str) -> Optional[str]:
        """
        enum定数から型名を取得
        
        Args:
            constant: enum定数名
        
        Returns:
            enum型名、見つからない場合はNone
        """
        return self._enum_constant_to_type.get(constant)
    
    def get_all_enum_values(self, enum_type: str) -> List[str]:
        """
        指定されたenum型のすべての定数を取得
        
        Args:
            enum_type: enum型名
        
        Returns:
            定数名のリスト
        """
        if not self.parsed_data or not hasattr(self.parsed_data, 'enums'):
            return []
        
        return self.parsed_data.enums.get(enum_type, [])
    
    def get_macro_value(self, macro_name: str) -> Optional[str]:
        """
        マクロの定義値を取得
        
        Args:
            macro_name: マクロ名
        
        Returns:
            マクロの値、見つからない場合はNone
        """
        if not self.parsed_data or not hasattr(self.parsed_data, 'macros'):
            return None
        
        return self.parsed_data.macros.get(macro_name)
    
    def resolve_different_value(self, value: str, max_value: int = None, var_type: str = None) -> Tuple[str, str]:
        """
        指定された値と異なる値を解決
        
        Args:
            value: 比較対象の値（数値、識別子、enum定数）
            max_value: 最大値制約（ビットフィールド等の場合に指定）(v4.2.1追加)
            var_type: 変数の型（フォールバック値の型を決定）(v4.3.0追加)
        
        Returns:
            (異なる値, コメント) のタプル
        
        Examples:
            >>> resolver.resolve_different_value("10")
            ("11", "10と異なる値")
            >>> resolver.resolve_different_value("Utm24")
            ("Utm25", "Utm24と異なるenum値")
            >>> resolver.resolve_different_value("UtD1")
            ("256", "UtD1(=255)と異なる値")
            >>> resolver.resolve_different_value("3", max_value=3)  # 2ビットフィールド
            ("2", "3と異なる値（最大値3考慮）")
        """
        if not value:
            # v4.3.0: 型に応じたフォールバック値を使用
            fallback = self.get_fallback_value_for_type(var_type) if var_type else self.FALLBACK_VALUE_SHORT
            return (fallback, "不明な値と異なる値")
        
        value = value.strip()
        
        # 1. 数値の場合
        if self.is_numeric(value):
            result = self._resolve_numeric_different(value, max_value)
            return result
        
        # 2. enum定数の場合
        if self.is_enum_constant(value):
            result = self._resolve_enum_different(value)
            return result
        
        # 3. マクロ定数の場合
        if self.is_macro_constant(value):
            result = self._resolve_macro_different(value, max_value)
            return result
        
        # 4. 不明な識別子の場合（フォールバック）
        self.logger.debug(f"Unknown identifier: {value}, using fallback")
        # v4.3.0: 型に応じたフォールバック値を使用
        fallback = self.get_fallback_value_for_type(var_type) if var_type else self.FALLBACK_VALUE_SHORT
        return (fallback, f"{value}と異なる値（不明な識別子）")
    
    def _resolve_numeric_different(self, value: str, max_value: int = None) -> Tuple[str, str]:
        """
        数値と異なる値を解決
        
        v4.2.1: max_value制約を追加（ビットフィールド対応）
        
        Args:
            value: 数値文字列
            max_value: 最大値制約（ビットフィールド等の場合）
        
        Returns:
            (異なる値, コメント) のタプル
        """
        num = self.parse_numeric(value)
        if num is None:
            return (self.FALLBACK_VALUE_SHORT, f"{value}と異なる値")
        
        # max_value制約がある場合（ビットフィールド等）
        if max_value is not None:
            if num >= max_value:
                # 最大値以上の場合は-1
                different = num - 1 if num > 0 else 0
                return (str(different), f"{value}と異なる値（最大値{max_value}考慮）")
            elif num == 0:
                # 0の場合は+1（ただし最大値を超えない）
                different = min(1, max_value)
                return (str(different), f"0と異なる値（最大値{max_value}考慮）")
            else:
                # 通常は+1、ただし最大値を超えないように
                different = num + 1
                if different > max_value:
                    different = num - 1
                return (str(different), f"{value}と異なる値（最大値{max_value}考慮）")
        
        # max_value制約がない場合（従来の動作）
        # 0の場合は1を返す
        if num == 0:
            return ("1", "0と異なる値")
        
        # 正の数の場合は+1
        if num > 0:
            different = num + 1
            # オーバーフロー対策
            if different > 0xFFFFFFFF:
                different = num - 1
            return (str(different), f"{value}と異なる値")
        
        # 負の数の場合は-1
        different = num - 1
        return (str(different), f"{value}と異なる値")
    
    def _resolve_enum_different(self, value: str) -> Tuple[str, str]:
        """
        enum定数と異なる値を解決
        
        Args:
            value: enum定数名
        
        Returns:
            (異なる値, コメント) のタプル
        """
        enum_type = self.get_enum_type(value)
        if not enum_type:
            # enum型が不明な場合、数値0を返す（型推論に任せる）
            return ("0", f"{value}と異なるenum値")
        
        all_values = self.get_all_enum_values(enum_type)
        if not all_values:
            return ("0", f"{value}と異なるenum値")
        
        # 自分以外の値を取得
        other_values = [v for v in all_values if v != value]
        
        if other_values:
            # 最初の異なる値を使用
            different = other_values[0]
            return (different, f"{value}と異なるenum値({enum_type})")
        
        # 同じenumに他の値がない場合（単一値enum）
        return ("0", f"{value}と異なる値（単一値enum）")
    
    def _resolve_macro_different(self, value: str, max_value: int = None) -> Tuple[str, str]:
        """
        マクロ定数と異なる値を解決
        
        v4.2.1: max_value制約を追加（ビットフィールド対応）
        
        Args:
            value: マクロ名
            max_value: 最大値制約（ビットフィールド等の場合）
        
        Returns:
            (異なる値, コメント) のタプル
        """
        macro_value = self.get_macro_value(value)
        if not macro_value:
            return (self.FALLBACK_VALUE_SHORT, f"{value}と異なる値")
        
        # マクロの値が数値の場合
        if self.is_numeric(macro_value):
            num = self.parse_numeric(macro_value)
            if num is not None:
                # max_value制約がある場合
                if max_value is not None:
                    if num >= max_value:
                        different = num - 1 if num > 0 else 0
                    elif num == 0:
                        different = min(1, max_value)
                    else:
                        different = num + 1
                        if different > max_value:
                            different = num - 1
                    return (str(different), f"{value}(={macro_value})と異なる値（最大値{max_value}考慮）")
                else:
                    different = num + 1 if num >= 0 else num - 1
                    return (str(different), f"{value}(={macro_value})と異なる値")
        
        # マクロの値が別のマクロや識別子の場合
        # 再帰的に解決を試みる（深さ制限付き）
        if self.is_macro_constant(macro_value):
            # 循環参照を避けるため、1段階のみ展開
            inner_value = self.get_macro_value(macro_value)
            if inner_value and self.is_numeric(inner_value):
                num = self.parse_numeric(inner_value)
                if num is not None:
                    # max_value制約がある場合
                    if max_value is not None:
                        if num >= max_value:
                            different = num - 1 if num > 0 else 0
                        elif num == 0:
                            different = min(1, max_value)
                        else:
                            different = num + 1
                            if different > max_value:
                                different = num - 1
                        return (str(different), f"{value}(={macro_value}={inner_value})と異なる値（最大値{max_value}考慮）")
                    else:
                        different = num + 1 if num >= 0 else num - 1
                        return (str(different), f"{value}(={macro_value}={inner_value})と異なる値")
        
        return (self.FALLBACK_VALUE_SHORT, f"{value}と異なる値")
    
    def resolve_equal_value(self, value: str) -> Tuple[str, str]:
        """
        指定された値と等しい値を解決
        
        Args:
            value: 比較対象の値
        
        Returns:
            (等しい値, コメント) のタプル
        """
        if not value:
            return ("0", "値を設定")
        
        value = value.strip()
        
        # そのまま返す（等しい値）
        if self.is_numeric(value) or self.is_enum_constant(value):
            return (value, f"{value}と等しい値")
        
        if self.is_macro_constant(value):
            return (value, f"{value}と等しい値")
        
        # 不明な識別子の場合もそのまま返す
        return (value, f"{value}と等しい値")
    
    def get_boolean_init_value(self, truth: str) -> Tuple[str, str]:
        """
        ブール条件の初期化値を取得
        
        Args:
            truth: 真偽 ('T' or 'F')
        
        Returns:
            (値, コメント) のタプル
        """
        if truth == 'T':
            return ("1", "真")
        else:
            return ("0", "偽")
    
    def get_bitfield_init_value(self, truth: str, bit_width: int = 1) -> Tuple[str, str]:
        """
        ビットフィールドの初期化値を取得
        
        Args:
            truth: 真偽 ('T' or 'F')
            bit_width: ビット幅
        
        Returns:
            (値, コメント) のタプル
        """
        max_val = (1 << bit_width) - 1
        
        if truth == 'T':
            return ("1", f"真 (ビット幅: {bit_width}, 最大値: 0x{max_val:X})")
        else:
            return ("0", f"偽 (ビット幅: {bit_width})")
    
    def resolve_smaller_value(self, value: str) -> Tuple[str, str]:
        """
        指定された値より小さい値を解決 (v4.2.0追加)
        
        Args:
            value: 比較対象の値（数値、識別子、enum定数）
        
        Returns:
            (より小さい値, コメント) のタプル
        """
        if not value:
            return ("0", "不明な値より小さい値")
        
        value = value.strip()
        
        # 1. 数値の場合
        if self.is_numeric(value):
            num = self.parse_numeric(value)
            if num is not None:
                smaller = num - 1
                return (str(smaller), f"{value}より小さい値")
        
        # 2. マクロ定数の場合
        if self.is_macro_constant(value):
            macro_val = self.get_macro_value(value)
            if macro_val and self.is_numeric(macro_val):
                num = self.parse_numeric(macro_val)
                if num is not None:
                    smaller = num - 1
                    return (str(smaller), f"{value}(={macro_val})より小さい値")
        
        # 3. 不明な識別子の場合
        return ("0", f"{value}より小さい値（境界値）")
    
    def resolve_larger_value(self, value: str) -> Tuple[str, str]:
        """
        指定された値より大きい値を解決 (v4.2.0追加)
        
        Args:
            value: 比較対象の値（数値、識別子、enum定数）
        
        Returns:
            (より大きい値, コメント) のタプル
        """
        if not value:
            return ("1", "不明な値より大きい値")
        
        value = value.strip()
        
        # 1. 数値の場合
        if self.is_numeric(value):
            num = self.parse_numeric(value)
            if num is not None:
                larger = num + 1
                return (str(larger), f"{value}より大きい値")
        
        # 2. マクロ定数の場合
        if self.is_macro_constant(value):
            macro_val = self.get_macro_value(value)
            if macro_val and self.is_numeric(macro_val):
                num = self.parse_numeric(macro_val)
                if num is not None:
                    larger = num + 1
                    return (str(larger), f"{value}(={macro_val})より大きい値")
        
        # 3. 不明な識別子の場合
        return (self.FALLBACK_VALUE_SHORT, f"{value}より大きい値（境界値）")
    
    def get_bitfield_max_value(self, var_path: str) -> int:
        """
        構造体メンバーパスからビットフィールドの最大値を取得 (v4.2.1追加)
        
        Args:
            var_path: 変数パス（例: "Utx116.Utm6.Utm7" または "Utm7"）
        
        Returns:
            最大値（ビットフィールドでない場合はNone）
        """
        if not self.parsed_data or not hasattr(self.parsed_data, 'bitfields'):
            return None
        
        # メンバー名を抽出（パスの最後の部分）
        member_name = var_path.split('.')[-1] if '.' in var_path else var_path
        
        # bitfieldsディクショナリから検索
        for key, bitfield_info in self.parsed_data.bitfields.items():
            # メンバー名でマッチ
            if bitfield_info.member_name == member_name:
                return bitfield_info.get_max_value()
            # キー自体がメンバー名の場合
            if key == member_name:
                return bitfield_info.get_max_value()
        
        return None
    
    def get_bitfield_info(self, var_path: str):
        """
        構造体メンバーパスからビットフィールド情報を取得 (v4.2.1追加)
        
        Args:
            var_path: 変数パス（例: "Utx116.Utm6.Utm7" または "Utm7"）
        
        Returns:
            BitFieldInfoオブジェクト（ビットフィールドでない場合はNone）
        """
        if not self.parsed_data or not hasattr(self.parsed_data, 'bitfields'):
            return None
        
        # メンバー名を抽出（パスの最後の部分）
        member_name = var_path.split('.')[-1] if '.' in var_path else var_path
        
        # bitfieldsディクショナリから検索
        for key, bitfield_info in self.parsed_data.bitfields.items():
            # メンバー名でマッチ
            if bitfield_info.member_name == member_name:
                return bitfield_info
            # キー自体がメンバー名の場合
            if key == member_name:
                return bitfield_info
        
        return None
    
    def get_variable_type(self, var_path: str) -> Optional[str]:
        """
        変数パスから型情報を取得 (v4.3.0追加)
        
        Args:
            var_path: 変数パス（例: "Utx116" または "Utx116.Utm6.Utm7" または "local_var"）
        
        Returns:
            型名（見つからない場合はNone）
        """
        if not self.parsed_data:
            return None
        
        # ルート変数名を抽出
        root_var = var_path.split('.')[0] if '.' in var_path else var_path
        # 配列インデックスを除去
        root_var = re.sub(r'\[\d+\]', '', root_var)
        
        # 1. グローバル変数から検索
        if hasattr(self.parsed_data, 'variables') and self.parsed_data.variables:
            for var_info in self.parsed_data.variables:
                if var_info.name == root_var:
                    return var_info.var_type
        
        # 2. ローカル変数から検索
        if hasattr(self.parsed_data, 'local_variables') and self.parsed_data.local_variables:
            for var_name, var_info in self.parsed_data.local_variables.items():
                if var_name == root_var:
                    return var_info.var_type
        
        # 3. 構造体メンバーの場合、末端メンバーの型を取得
        if '.' in var_path:
            member_type = self._get_struct_member_type(var_path)
            if member_type:
                return member_type
        
        return None
    
    def _get_struct_member_type(self, var_path: str) -> Optional[str]:
        """
        構造体メンバーパスから末端メンバーの型を取得 (v4.3.0追加)
        
        Args:
            var_path: 構造体メンバーパス（例: "Utx116.Utm6.Utm7"）
        
        Returns:
            型名（見つからない場合はNone）
        """
        if not self.parsed_data:
            return None
        
        # ビットフィールドの場合
        bitfield_info = self.get_bitfield_info(var_path)
        if bitfield_info:
            return bitfield_info.base_type
        
        # 構造体定義から検索
        if hasattr(self.parsed_data, 'struct_definitions') and self.parsed_data.struct_definitions:
            parts = var_path.split('.')
            if len(parts) < 2:
                return None
            
            # 最後のメンバー名
            member_name = parts[-1]
            
            # 構造体定義を検索
            for struct_def in self.parsed_data.struct_definitions:
                if hasattr(struct_def, 'members'):
                    for member in struct_def.members:
                        if hasattr(member, 'name') and member.name == member_name:
                            if hasattr(member, 'type'):
                                return member.type
                            elif hasattr(member, 'member_type'):
                                return member.member_type
        
        return None
    
    def get_fallback_value_for_type(self, var_type: str) -> str:
        """
        型に応じたフォールバック値を返す (v4.3.0追加)
        
        Args:
            var_type: 変数の型（例: "uint8_t", "int", "Utx10"）
        
        Returns:
            型に適したフォールバック値
        """
        if not var_type:
            return self.FALLBACK_VALUE_SHORT
        
        # 型文字列をクリーンアップ
        clean_type = var_type.replace('const ', '').replace('volatile ', '').strip()
        
        # ポインタ型
        if '*' in clean_type:
            return 'NULL'
        
        # 配列型（[]を含む）
        if '[' in clean_type:
            # 基底型を抽出
            base_type = clean_type.split('[')[0].strip()
            return self.get_fallback_value_for_type(base_type)
        
        # 型別フォールバック値テーブルから検索
        if clean_type in self.FALLBACK_VALUES_BY_TYPE:
            return self.FALLBACK_VALUES_BY_TYPE[clean_type]
        
        # unsigned/signed修飾子付きの場合
        for base_type, value in self.FALLBACK_VALUES_BY_TYPE.items():
            if base_type in clean_type:
                return value
        
        # ビットフィールドの場合（型名からビット幅を推測）
        # uint16_t等の場合はテーブルにあるはず
        
        # 構造体/共用体型の場合はデフォルト値
        # （個別メンバーの初期化が必要なため、ここでは簡易的に0を返す）
        if any(keyword in clean_type.lower() for keyword in ['struct', 'union']):
            return '{0}'
        
        # enum型の場合
        if 'enum' in clean_type.lower():
            return '0'
        
        # typedef型の場合、基底型を探す
        if self.parsed_data and hasattr(self.parsed_data, 'typedefs'):
            for typedef_info in self.parsed_data.typedefs:
                if hasattr(typedef_info, 'name') and typedef_info.name == clean_type:
                    if hasattr(typedef_info, 'base_type'):
                        return self.get_fallback_value_for_type(typedef_info.base_type)
        
        # デフォルト
        return self.FALLBACK_VALUE_SHORT
    
    def get_max_value_for_type(self, var_type: str) -> Optional[int]:
        """
        型に応じた最大値を返す (v4.3.0追加)
        
        Args:
            var_type: 変数の型（例: "uint8_t", "int16_t"）
        
        Returns:
            型の最大値（不明な場合はNone）
        """
        if not var_type:
            return None
        
        # 型文字列をクリーンアップ
        clean_type = var_type.replace('const ', '').replace('volatile ', '').strip()
        
        # 符号なし整数型の最大値
        unsigned_max = {
            'uint8_t': 0xFF,
            'unsigned char': 0xFF,
            'uint16_t': 0xFFFF,
            'unsigned short': 0xFFFF,
            'uint32_t': 0xFFFFFFFF,
            'unsigned int': 0xFFFFFFFF,
            'unsigned long': 0xFFFFFFFF,
            'uint64_t': 0xFFFFFFFFFFFFFFFF,
            'unsigned long long': 0xFFFFFFFFFFFFFFFF,
        }
        
        # 符号付き整数型の最大値
        signed_max = {
            'int8_t': 0x7F,
            'signed char': 0x7F,
            'char': 0x7F,
            'int16_t': 0x7FFF,
            'short': 0x7FFF,
            'int32_t': 0x7FFFFFFF,
            'int': 0x7FFFFFFF,
            'long': 0x7FFFFFFF,
            'int64_t': 0x7FFFFFFFFFFFFFFF,
            'long long': 0x7FFFFFFFFFFFFFFF,
        }
        
        if clean_type in unsigned_max:
            return unsigned_max[clean_type]
        if clean_type in signed_max:
            return signed_max[clean_type]
        
        return None


# メインブロック（テスト用）
if __name__ == "__main__":
    print("=" * 70)
    print("ValueResolver のテスト")
    print("=" * 70)
    print()
    
    # モックのparsed_dataを作成
    class MockParsedData:
        def __init__(self):
            self.enums = {
                'Utx76': ['Utm24', 'Utm25', 'Utm26', 'Utm27', 'Utm28', 'Utm29', 'Utm30', 'Utm31', 'Utx11'],
                'Utx110': ['Utm46', 'Utm47', 'Utm48', 'Utm49', 'Utx51'],
            }
            self.enum_values = ['Utm24', 'Utm25', 'Utm26', 'Utm27', 'Utm28', 'Utm29', 
                               'Utm30', 'Utm31', 'Utx11', 'Utm46', 'Utm47', 'Utm48', 'Utm49', 'Utx51']
            self.macros = {
                'UtD1': '255',
                'UtD2': '251',
                'UtD3': '3',
                'UtD4': '8',
            }
    
    parsed_data = MockParsedData()
    resolver = ValueResolver(parsed_data)
    
    # テスト1: 数値判定
    print("1. 数値判定のテスト")
    test_values = ["123", "0xFF", "-42", "ENUM_VALUE", "0", "3.14"]
    for val in test_values:
        result = resolver.is_numeric(val)
        print(f"  is_numeric('{val}'): {result}")
    print()
    
    # テスト2: enum定数判定
    print("2. enum定数判定のテスト")
    test_values = ["Utm24", "Utm47", "UNKNOWN", "UtD1"]
    for val in test_values:
        result = resolver.is_enum_constant(val)
        print(f"  is_enum_constant('{val}'): {result}")
    print()
    
    # テスト3: マクロ定数判定
    print("3. マクロ定数判定のテスト")
    test_values = ["UtD1", "UtD3", "UNKNOWN", "Utm24"]
    for val in test_values:
        result = resolver.is_macro_constant(val)
        print(f"  is_macro_constant('{val}'): {result}")
    print()
    
    # テスト4: 異なる値の解決
    print("4. 異なる値の解決テスト")
    test_values = ["10", "0", "-5", "0xFF", "Utm24", "Utm47", "UtD1", "UNKNOWN"]
    for val in test_values:
        different, comment = resolver.resolve_different_value(val)
        print(f"  '{val}' -> '{different}' // {comment}")
    print()
    
    # テスト5: ブール値の初期化
    print("5. ブール値の初期化テスト")
    for truth in ['T', 'F']:
        value, comment = resolver.get_boolean_init_value(truth)
        print(f"  truth='{truth}' -> '{value}' // {comment}")
    print()
    
    # テスト6: ビットフィールドの初期化
    print("6. ビットフィールドの初期化テスト")
    for truth in ['T', 'F']:
        for width in [1, 3, 8]:
            value, comment = resolver.get_bitfield_init_value(truth, width)
            print(f"  truth='{truth}', width={width} -> '{value}' // {comment}")
    print()
    
    print("=" * 70)
    print("✓ ValueResolverのテストが完了しました")
    print("=" * 70)
