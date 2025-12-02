"""
MockGeneratorモジュール（v4.1.2）

モック/スタブ関数を生成
v4.0: 元の関数と同じシグネチャでモックを生成（リンカ互換）
v4.1.2: 構造体型変数の初期化をmemset対応
"""

import sys
import os
from typing import List, Dict, Optional, Set

# パスを追加
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))
from src.utils import setup_logger
from src.data_structures import ParsedData, MockFunction, FunctionSignature


class MockGenerator:
    """モックジェネレータ（v4.1.2: 構造体型初期化対応）"""
    
    # プリミティブ型のセット（v4.1.2追加）
    PRIMITIVE_TYPES: Set[str] = {
        # 標準整数型
        'int', 'short', 'long', 'char',
        'signed', 'unsigned',
        'signed int', 'unsigned int',
        'signed short', 'unsigned short',
        'signed long', 'unsigned long',
        'signed char', 'unsigned char',
        'long long', 'unsigned long long',
        # 固定幅整数型
        'int8_t', 'int16_t', 'int32_t', 'int64_t',
        'uint8_t', 'uint16_t', 'uint32_t', 'uint64_t',
        # ブール型
        'bool', '_Bool',
        # 浮動小数点型
        'float', 'double', 'long double',
        # その他
        'size_t', 'ptrdiff_t', 'intptr_t', 'uintptr_t',
        'void',
    }
    
    def __init__(self):
        """初期化"""
        self.logger = setup_logger(__name__)
        self.mock_functions: List[MockFunction] = []
        self._needs_string_h = False  # memset使用フラグ（v4.1.2追加）
    
    def generate_mocks(self, parsed_data: ParsedData) -> str:
        """
        モック/スタブコードを生成
        
        v4.0: 元の関数と同じシグネチャでモックを生成
        
        Args:
            parsed_data: 解析済みデータ
        
        Returns:
            モックコード
        """
        self.logger.info("v4.0: モック/スタブコードの生成を開始（シグネチャ一致）")
        
        # 外部関数からモック関数リストを作成
        self.mock_functions = []
        self._needs_string_h = False
        
        for func_name in parsed_data.external_functions:
            # シグネチャ情報を取得（なければデフォルト）
            signature = parsed_data.function_signatures.get(func_name)
            mock_func = self._create_mock_function(func_name, signature)
            self.mock_functions.append(mock_func)
            
            # 構造体型があるかチェック（v4.1.2）
            if not self._is_primitive_type(mock_func.return_type) and mock_func.return_type != 'void':
                self._needs_string_h = True
            for param in mock_func.parameters:
                if not self._is_primitive_type(param['type']):
                    self._needs_string_h = True
        
        # コードを生成
        code_parts = []
        
        # 1. モック用グローバル変数
        code_parts.append(self.generate_mock_variables())
        
        # 2. モック関数の実装
        code_parts.append(self.generate_mock_functions())
        
        # 3. リセット関数
        code_parts.append(self.generate_reset_function())
        
        self.logger.info(f"v4.0: モック/スタブコードの生成が完了: {len(self.mock_functions)}個")
        
        return '\n\n'.join(code_parts)
    
    def needs_string_h(self) -> bool:
        """
        memset使用のためstring.hが必要かどうか（v4.1.2追加）
        
        Returns:
            string.hが必要ならTrue
        """
        return self._needs_string_h
    
    def _is_primitive_type(self, type_name: str) -> bool:
        """
        プリミティブ型かどうかを判定（v4.1.2追加）
        
        Args:
            type_name: 型名
        
        Returns:
            プリミティブ型ならTrue
        """
        if not type_name:
            return True
        
        # ポインタ型はプリミティブとして扱う（NULLで初期化可能）
        if '*' in type_name:
            return True
        
        # const, volatileなどの修飾子を除去
        cleaned = type_name.replace('const', '').replace('volatile', '').strip()
        
        # プリミティブ型セットに含まれるかチェック
        return cleaned in self.PRIMITIVE_TYPES
    
    def _is_pointer_type(self, type_name: str) -> bool:
        """
        ポインタ型かどうかを判定（v4.1.2追加）
        
        Args:
            type_name: 型名
        
        Returns:
            ポインタ型ならTrue
        """
        return '*' in type_name if type_name else False
    
    def _get_init_code(self, var_name: str, type_name: str) -> str:
        """
        変数の初期化コードを取得（v4.1.2追加）
        
        Args:
            var_name: 変数名
            type_name: 型名
        
        Returns:
            初期化コード（末尾のセミコロン含む）
        """
        if type_name == 'void':
            return ""
        
        if self._is_pointer_type(type_name):
            return f"{var_name} = NULL;"
        elif self._is_primitive_type(type_name):
            return f"{var_name} = 0;"
        else:
            # 構造体/union型 - memsetを使用
            self._needs_string_h = True
            return f"memset(&{var_name}, 0, sizeof({var_name}));"
    
    def _create_mock_function(self, func_name: str, 
                              signature: Optional[FunctionSignature] = None) -> MockFunction:
        """
        モック関数情報を作成（v4.0: シグネチャ対応）
        
        Args:
            func_name: 関数名
            signature: 関数シグネチャ（Noneの場合はデフォルト）
        
        Returns:
            MockFunction
        """
        if signature:
            return_type = signature.return_type
            parameters = signature.parameters
            self.logger.debug(f"シグネチャ情報あり: {func_name} -> {return_type}")
        else:
            # シグネチャ不明時のフォールバック
            self.logger.warning(f"関数 {func_name} のシグネチャが不明です。デフォルト(int)を使用します")
            return_type = self._guess_return_type(func_name)
            parameters = []
        
        return MockFunction(
            name=func_name,
            return_type=return_type,
            parameters=parameters,
            return_variable=f"mock_{func_name}_return_value",
            call_count_variable=f"mock_{func_name}_call_count"
        )
    
    def _guess_return_type(self, func_name: str) -> str:
        """
        関数名から戻り値の型を推定（フォールバック用）
        
        Args:
            func_name: 関数名
        
        Returns:
            型名
        """
        # 簡易的な型推定（シグネチャがない場合のみ使用）
        if func_name.startswith('f'):
            return 'uint16_t'
        elif func_name.startswith('mx'):
            return 'mx26'  # enum型を仮定
        else:
            return 'int'
    
    def generate_mock_variables(self) -> str:
        """
        モック用グローバル変数を生成（v4.0: パラメータキャプチャ対応）
        
        Returns:
            変数定義のコード
        """
        lines = ["// ===== モック・スタブ用グローバル変数 ====="]
        
        for mock_func in self.mock_functions:
            # 戻り値変数（void型でない場合のみ）
            if mock_func.return_type != "void":
                lines.append(f"static {mock_func.return_type} {mock_func.return_variable};")
            
            # 呼び出し回数カウンタ
            lines.append(f"static int {mock_func.call_count_variable};")
            
            # パラメータキャプチャ変数（v4.0新規）
            for param in mock_func.parameters:
                param_var = f"mock_{mock_func.name}_param_{param['name']}"
                lines.append(f"static {param['type']} {param_var};")
            
            lines.append("")
        
        return '\n'.join(lines)
    
    def generate_mock_functions(self) -> str:
        """
        モック関数の実装を生成（v4.0: 元の関数と同じシグネチャ）
        
        Returns:
            モック関数のコード
        """
        lines = ["// ===== モック・スタブ実装 ====="]
        lines.append("")
        
        for mock_func in self.mock_functions:
            # 関数コメント
            lines.append(f"/**")
            lines.append(f" * {mock_func.name}のモック")
            lines.append(f" */")
            
            # パラメータ文字列を構築
            if mock_func.parameters:
                params_str = ", ".join(
                    f"{p['type']} {p['name']}" for p in mock_func.parameters
                )
            else:
                params_str = "void"
            
            # v4.0: 元の関数と同じ名前・シグネチャ（staticなし、mock_プレフィックスなし）
            lines.append(f"{mock_func.return_type} {mock_func.name}({params_str}) {{")
            lines.append(f"    {mock_func.call_count_variable}++;")
            
            # パラメータをキャプチャ（v4.0新規）
            for param in mock_func.parameters:
                param_var = f"mock_{mock_func.name}_param_{param['name']}"
                lines.append(f"    {param_var} = {param['name']};")
            
            # void型でない場合のみreturn文を生成
            if mock_func.return_type != "void":
                lines.append(f"    return {mock_func.return_variable};")
            lines.append(f"}}")
            lines.append("")
        
        return '\n'.join(lines)
    
    def generate_reset_function(self) -> str:
        """
        モックをリセットする関数を生成
        
        v4.0: パラメータ変数も初期化
        v4.1.2: 構造体型はmemsetで初期化
        
        Returns:
            リセット関数のコード
        """
        lines = ["// ===== モックリセット関数 ====="]
        lines.append("")
        lines.append("/**")
        lines.append(" * 全てのモックをリセット")
        lines.append(" */")
        lines.append("static void reset_all_mocks(void) {")
        
        for mock_func in self.mock_functions:
            # 戻り値変数（void型でない場合のみ）
            if mock_func.return_type != "void":
                init_code = self._get_init_code(
                    mock_func.return_variable, 
                    mock_func.return_type
                )
                if init_code:
                    lines.append(f"    {init_code}")
            
            # 呼び出し回数カウンタ（常にint型）
            lines.append(f"    {mock_func.call_count_variable} = 0;")
            
            # パラメータキャプチャ変数もリセット（v4.0新規、v4.1.2で型対応）
            for param in mock_func.parameters:
                param_var = f"mock_{mock_func.name}_param_{param['name']}"
                init_code = self._get_init_code(param_var, param['type'])
                if init_code:
                    lines.append(f"    {init_code}")
        
        lines.append("}")
        
        return '\n'.join(lines)
    
    def generate_prototypes(self) -> str:
        """
        モック関数のプロトタイプ宣言を生成
        
        v4.0: 元の関数と同名なので、ここでは生成しない
        （元のプロトタイプ宣言をそのまま使用）
        
        Returns:
            プロトタイプ宣言のコード
        """
        # v4.0ではモックのプロトタイプは不要（元のプロトタイプが使われる）
        lines = ["// ===== プロトタイプ宣言（モック・スタブ） ====="]
        lines.append("// v4.0: モックは元の関数を置き換えるため、元のプロトタイプ宣言を使用")
        lines.append("static void reset_all_mocks(void);")
        
        return '\n'.join(lines)
    
    def generate_setup_code(self, test_case_no: int) -> str:
        """
        テストケースのセットアップコードを生成
        
        Args:
            test_case_no: テストケース番号
        
        Returns:
            セットアップコード
        """
        lines = []
        lines.append("    // モックをリセット")
        lines.append("    reset_all_mocks();")
        lines.append("")
        
        return '\n'.join(lines)
    
    def generate_assert_call_counts(self) -> str:
        """
        呼び出し回数のアサートコードを生成
        
        Returns:
            アサートコード
        """
        lines = []
        lines.append("    // 呼び出し回数の確認")
        
        for mock_func in self.mock_functions:
            lines.append(f"    // TEST_ASSERT_EQUAL(expected_count, {mock_func.call_count_variable});  // TODO: 期待回数を設定後コメント解除")
        
        return '\n'.join(lines)
    
    def generate_param_assertions(self) -> str:
        """
        パラメータ値のアサートコードを生成（v4.0新規）
        
        Returns:
            アサートコード
        """
        lines = []
        lines.append("    // パラメータ値の確認")
        
        for mock_func in self.mock_functions:
            for param in mock_func.parameters:
                param_var = f"mock_{mock_func.name}_param_{param['name']}"
                lines.append(f"    // TEST_ASSERT_EQUAL(expected_{param['name']}, {param_var});  // TODO: 期待値を設定後コメント解除")
        
        return '\n'.join(lines)


if __name__ == "__main__":
    # MockGeneratorのテスト
    print("=" * 70)
    print("MockGenerator v4.1.2 のテスト（構造体型初期化対応）")
    print("=" * 70)
    print()
    
    from src.data_structures import ParsedData, FunctionSignature
    
    # テスト用のParseDataを作成（v4.1.2: 構造体型を含む）
    parsed_data = ParsedData(
        file_name="test.c",
        function_name="test_func",
        external_functions=['Utf8', 'Utf9', 'Utx167', 'Utx69']
    )
    
    # シグネチャ情報を設定（構造体型を含む）
    parsed_data.function_signatures = {
        'Utf8': FunctionSignature(
            name='Utf8',
            return_type='uint8_t',  # プリミティブ型
            parameters=[]
        ),
        'Utf9': FunctionSignature(
            name='Utf9',
            return_type='uint16_t',  # プリミティブ型
            parameters=[
                {'type': 'uint8_t', 'name': 'param1'},
                {'type': 'int', 'name': 'param2'}
            ]
        ),
        'Utx167': FunctionSignature(
            name='Utx167',
            return_type='Utx10',  # 構造体/union型
            parameters=[
                {'type': 'Utx10', 'name': 'Utx123'}  # 構造体型パラメータ
            ]
        ),
        'Utx69': FunctionSignature(
            name='Utx69',
            return_type='Utx10',  # 構造体/union型
            parameters=[
                {'type': 'Utx10', 'name': 'Utx123'},  # 構造体型
                {'type': 'Utx168', 'name': 'Utx128'},  # 構造体型
                {'type': 'uint8_t*', 'name': 'ptr'}  # ポインタ型
            ]
        )
    }
    
    # モックを生成
    generator = MockGenerator()
    mock_code = generator.generate_mocks(parsed_data)
    
    print("生成されたモックコード:")
    print("=" * 70)
    print(mock_code)
    print("=" * 70)
    print()
    
    # memset使用確認
    print(f"string.h が必要: {generator.needs_string_h()}")
    print()
    
    # プロトタイプ宣言
    print("プロトタイプ宣言:")
    print("=" * 70)
    print(generator.generate_prototypes())
    print("=" * 70)
    print()
    
    # セットアップコード
    print("セットアップコード:")
    print("=" * 70)
    print(generator.generate_setup_code(1))
    print("=" * 70)
    print()
    
    # リセット関数の確認
    print("リセット関数（v4.1.2: 構造体型はmemset使用）:")
    print("=" * 70)
    print(generator.generate_reset_function())
    print("=" * 70)
    print()
    
    print("✓ MockGenerator v4.1.2 が正常に動作しました")
