"""
MockGeneratorモジュール（v4.3.4）

モック/スタブ関数を生成
v4.0: 元の関数と同じシグネチャでモックを生成（リンカ互換）
v4.1.2: 構造体型変数の初期化をmemset対応
v4.3.4: const維持、ポインタのメモリコピー対応
v5.1.13: パススルーモック対応（入力値をそのまま返す関数）
"""

import sys
import os
from typing import List, Dict, Optional, Set

# パスを追加
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))
from src.utils import setup_logger
from src.data_structures import ParsedData, MockFunction, FunctionSignature


class MockGenerator:
    """モックジェネレータ（v4.3.4: const維持、ポインタメモリコピー対応）"""
    
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
    
    # v5.1.13: パススルー関数（第1引数をそのまま返す関数）
    PASSTHROUGH_FUNCTIONS: Set[str] = {
        'clamp_value', 'clamp', 'clip', 'limit',
        'abs', 'labs', 'llabs', 'fabs', 'fabsf', 'fabsl',
        'min', 'max', 'MIN', 'MAX',
        'saturate', 'bound', 'constrain',
    }
    
    def __init__(self):
        """初期化"""
        self.logger = setup_logger(__name__)
        self.mock_functions: List[MockFunction] = []
        self._needs_string_h = False  # memset使用フラグ（v4.1.2追加）
        self._passthrough_functions: Set[str] = set(self.PASSTHROUGH_FUNCTIONS)  # v5.1.13
    
    def add_passthrough_function(self, func_name: str) -> None:
        """パススルー関数を追加（v5.1.13）"""
        self._passthrough_functions.add(func_name)
    
    def is_passthrough_function(self, func_name: str) -> bool:
        """パススルー関数かどうか判定（v5.1.13）"""
        return func_name in self._passthrough_functions
    
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
    
    def _get_base_type(self, type_name: str) -> str:
        """
        ポインタ型からベース型を取得（v4.3.4追加）
        
        例: "const net_msg_cmd_t *" → "net_msg_cmd_t"
        
        Args:
            type_name: 型名
        
        Returns:
            ベース型
        """
        if not type_name:
            return type_name
        
        # const を除去
        base = type_name.replace('const', '').strip()
        # * を除去
        base = base.replace('*', '').strip()
        # 余分なスペースを正規化
        base = ' '.join(base.split())
        
        return base
    
    def _remove_const_from_type(self, type_name: str) -> str:
        """
        型名からconst修飾子を除去（パラメータキャプチャ変数用）（v4.3.4追加）
        
        例: "const net_msg_cmd_t *" → "net_msg_cmd_t *"
        
        Args:
            type_name: 型名
        
        Returns:
            constを除去した型名
        """
        if not type_name:
            return type_name
        
        cleaned = type_name.replace('const ', '').replace(' const', '').replace('const', '')
        return ' '.join(cleaned.split())
    
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
        モック用グローバル変数を生成（v4.3.4: ポインタ用実データ変数追加）
        
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
            
            # パラメータキャプチャ変数（v4.3.4: ポインタ型は_data変数追加）
            for param in mock_func.parameters:
                param_var = f"mock_{mock_func.name}_param_{param['name']}"
                param_type = param['type']
                
                if self._is_pointer_type(param_type):
                    # ポインタ型の場合: 実データ用変数 + ポインタ変数
                    base_type = self._get_base_type(param_type)
                    lines.append(f"static {base_type} {param_var}_data;  // 実データ保持用")
                    # ポインタ変数（constなし）
                    non_const_type = self._remove_const_from_type(param_type)
                    lines.append(f"static {non_const_type} {param_var};  // ポインタ")
                else:
                    # 非ポインタ型: そのまま（constは除去）
                    non_const_type = self._remove_const_from_type(param_type)
                    lines.append(f"static {non_const_type} {param_var};")
            
            lines.append("")
        
        return '\n'.join(lines)
    
    def generate_mock_functions(self) -> str:
        """
        モック関数の実装を生成
        v4.3.4: const維持、ポインタのメモリコピー
        v4.3.4.1: static修飾子追加
        v5.1.13: パススルーモック対応（入力値をそのまま返す）
        
        Returns:
            モック関数のコード
        """
        lines = ["// ===== モック・スタブ実装 ====="]
        lines.append("")
        
        for mock_func in self.mock_functions:
            # 関数コメント
            is_passthrough = self.is_passthrough_function(mock_func.name)
            lines.append(f"/**")
            if is_passthrough:
                lines.append(f" * {mock_func.name}のモック（パススルー: 第1引数を返す）")
            else:
                lines.append(f" * {mock_func.name}のモック")
            lines.append(f" */")
            
            # パラメータ文字列を構築（v4.3.4: constをそのまま維持）
            if mock_func.parameters:
                params_str = ", ".join(
                    f"{p['type']} {p['name']}" for p in mock_func.parameters
                )
            else:
                params_str = "void"
            
            # v4.3.4.1: static修飾子を追加
            lines.append(f"static {mock_func.return_type} {mock_func.name}({params_str}) {{")
            lines.append(f"    {mock_func.call_count_variable}++;")
            
            # パラメータをキャプチャ（v4.3.4: ポインタはmemcpy）
            for param in mock_func.parameters:
                param_var = f"mock_{mock_func.name}_param_{param['name']}"
                param_type = param['type']
                param_name = param['name']
                
                if self._is_pointer_type(param_type):
                    # ポインタ型: NULLチェック + memcpy
                    base_type = self._get_base_type(param_type)
                    lines.append(f"    if ({param_name} != NULL) {{")
                    lines.append(f"        memcpy(&{param_var}_data, {param_name}, sizeof({base_type}));")
                    lines.append(f"    }}")
                    lines.append(f"    {param_var} = &{param_var}_data;")
                    self._needs_string_h = True  # memcpy使用
                else:
                    # 非ポインタ型: 単純コピー
                    lines.append(f"    {param_var} = {param_name};")
            
            # void型でない場合のみreturn文を生成
            if mock_func.return_type != "void":
                # v5.1.13: パススルー関数は第1引数をそのまま返す
                if is_passthrough and mock_func.parameters:
                    first_param = mock_func.parameters[0]['name']
                    lines.append(f"    return {first_param};  // パススルー")
                else:
                    lines.append(f"    return {mock_func.return_variable};")
            lines.append(f"}}")
            lines.append("")
        
        return '\n'.join(lines)
    
    def generate_reset_function(self) -> str:
        """
        モックをリセットする関数を生成
        
        v4.0: パラメータ変数も初期化
        v4.1.2: 構造体型はmemsetで初期化
        v4.3.4: ポインタ用実データも初期化
        
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
            
            # パラメータキャプチャ変数もリセット（v4.3.4: ポインタ用実データも初期化）
            for param in mock_func.parameters:
                param_var = f"mock_{mock_func.name}_param_{param['name']}"
                param_type = param['type']
                
                if self._is_pointer_type(param_type):
                    # ポインタ型: 実データとポインタ両方を初期化
                    base_type = self._get_base_type(param_type)
                    lines.append(f"    memset(&{param_var}_data, 0, sizeof({base_type}));")
                    lines.append(f"    {param_var} = NULL;")
                    self._needs_string_h = True  # memset使用
                else:
                    # 非ポインタ型
                    non_const_type = self._remove_const_from_type(param_type)
                    init_code = self._get_init_code(param_var, non_const_type)
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
    print("MockGenerator v4.3.4 のテスト（const維持、static追加、ポインタメモリコピー対応）")
    print("=" * 70)
    print()
    
    from src.data_structures import ParsedData, FunctionSignature
    
    # テスト用のParseDataを作成（v4.3.4: constポインタを含む）
    parsed_data = ParsedData(
        file_name="test.c",
        function_name="test_func",
        external_functions=['Utf8', 'net_set_cmd_res', 'process_buffer', 'send_message']
    )
    
    # シグネチャ情報を設定（v4.3.4: constポインタを含む）
    parsed_data.function_signatures = {
        'Utf8': FunctionSignature(
            name='Utf8',
            return_type='uint8_t',
            parameters=[]
        ),
        'net_set_cmd_res': FunctionSignature(
            name='net_set_cmd_res',
            return_type='void',
            parameters=[
                {'type': 'const net_msg_cmd_t *', 'name': 'inMsg13'}
            ]
        ),
        'process_buffer': FunctionSignature(
            name='process_buffer',
            return_type='int',
            parameters=[
                {'type': 'uint8_t *', 'name': 'buffer'},
                {'type': 'size_t', 'name': 'len'}
            ]
        ),
        'send_message': FunctionSignature(
            name='send_message',
            return_type='bool',
            parameters=[
                {'type': 'const msg_t *', 'name': 'msg'},
                {'type': 'int', 'name': 'priority'},
                {'type': 'const char *', 'name': 'dest'}
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
    
    # 確認ポイント
    print("確認ポイント:")
    print("-" * 70)
    print("1. const ポインタ引数に 'const' が維持されているか")
    print("2. ポインタ型パラメータに _data 変数が生成されているか")
    print("3. memcpy でデータをコピーしているか")
    print("4. NULLチェックがあるか")
    print("-" * 70)
    print()
    
    # 検証
    errors = []
    
    # 1. const 維持チェック
    if 'const net_msg_cmd_t *' not in mock_code:
        errors.append("ERROR: net_set_cmd_res の引数に const が維持されていない")
    if 'const msg_t *' not in mock_code:
        errors.append("ERROR: send_message の msg 引数に const が維持されていない")
    
    # 2. _data 変数チェック
    if 'mock_net_set_cmd_res_param_inMsg13_data' not in mock_code:
        errors.append("ERROR: _data 変数が生成されていない")
    
    # 3. memcpy チェック
    if 'memcpy(&mock_net_set_cmd_res_param_inMsg13_data' not in mock_code:
        errors.append("ERROR: memcpy が使用されていない")
    
    # 4. NULLチェック
    if 'if (inMsg13 != NULL)' not in mock_code:
        errors.append("ERROR: NULLチェックがない")
    
    if errors:
        print("検証結果: NG")
        for e in errors:
            print(f"  {e}")
    else:
        print("検証結果: OK")
        print("  ✓ const が維持されている")
        print("  ✓ _data 変数が生成されている")
        print("  ✓ memcpy が使用されている")
        print("  ✓ NULLチェックがある")
    
    print()
    print("✓ MockGenerator v4.3.4 テスト完了")
