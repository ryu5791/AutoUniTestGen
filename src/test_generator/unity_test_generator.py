"""
UnityTestGeneratorモジュール

全てのコンポーネントを統合してUnityテストコードを生成

v4.4:
- テスト対象関数をstaticに変換する機能を追加
- 外部関数のプロトタイプ宣言だけでなく、テスト対象関数もstaticに変換
"""

import sys
import os
from typing import Optional, List

# パスを追加
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))
from src.utils import setup_logger
from src.data_structures import ParsedData, TruthTableData, TestCode, TestCase
from src.test_generator.mock_generator import MockGenerator
from src.test_generator.test_function_generator import TestFunctionGenerator
from src.test_generator.prototype_generator import PrototypeGenerator
from src.test_generator.comment_generator import CommentGenerator
from src.code_extractor.code_extractor import CodeExtractor  # v2.2: 関数抽出機能


class UnityTestGenerator:
    """Unityテストジェネレータ"""
    
    def __init__(self, include_target_function: bool = True):
        """
        初期化
        
        Args:
            include_target_function: テスト対象関数の本体を含めるか（v2.2の新機能）
        """
        self.logger = setup_logger(__name__)
        self.mock_gen = MockGenerator()
        self.test_func_gen = TestFunctionGenerator()
        self.proto_gen = PrototypeGenerator()
        self.comment_gen = CommentGenerator()
        self.code_extractor = CodeExtractor()  # v2.2: 関数抽出機能
        self.include_target_function = include_target_function  # v2.2
    
    def generate(self, truth_table: TruthTableData, parsed_data: ParsedData, 
                 source_code: Optional[str] = None) -> TestCode:
        """
        Unityテストコードを生成
        
        Args:
            truth_table: 真偽表データ
            parsed_data: 解析済みデータ
            source_code: 元のソースコード（v2.2: 関数本体抽出用、Noneの場合は抽出しない）
        
        Returns:
            TestCode
        """
        self.logger.info("Unityテストコードの生成を開始")
        
        test_code = TestCode()
        
        # 1. ヘッダー
        test_code.header = self._generate_header(parsed_data)
        
        # 2. #include文
        test_code.includes = self._generate_includes()
        
        # 3. 型定義（v2.2: parsed_dataを渡して自動生成）
        test_code.type_definitions = self._generate_type_definitions(parsed_data)
        
        # 4. プロトタイプ宣言
        test_code.prototypes = self.proto_gen.generate_prototypes(truth_table, parsed_data)
        
        # 5. モック変数とモック関数
        mock_code = self.mock_gen.generate_mocks(parsed_data)
        parts = mock_code.split('\n\n')
        if len(parts) >= 2:
            test_code.mock_variables = parts[0]
            test_code.mock_functions = '\n\n'.join(parts[1:])
        else:
            test_code.mock_functions = mock_code
        
        # 6. テスト関数群
        test_code.test_functions = self._generate_all_test_functions(truth_table, parsed_data)
        
        # 7. setUp/tearDown (v5.0.0: static/global変数初期化追加)
        test_code.setup_teardown = self._generate_setup_teardown(parsed_data)
        
        # 8. v2.2: テスト対象関数の本体を抽出して追加
        if self.include_target_function and source_code:
            self.logger.info("v2.2: テスト対象関数の本体を抽出中...")
            target_code = self._extract_target_function(source_code, parsed_data.function_name)
            if target_code:
                test_code.target_function_code = target_code
                self.logger.info("✓ v2.2: テスト対象関数の本体を追加しました")
            else:
                self.logger.warning("✗ v2.2: テスト対象関数の本体が抽出できませんでした")
        
        # 9. v2.3: main関数を生成
        test_code.main_function = self._generate_main_function(truth_table, parsed_data)
        
        self.logger.info(f"Unityテストコードの生成が完了: {len(truth_table.test_cases)}個のテスト関数")
        
        return test_code
    
    def generate_standalone(self, truth_table: TruthTableData, parsed_data: ParsedData, 
                           source_code: str) -> str:
        """
        元のソースファイル全体にテストコードを追加したスタンドアロン版を生成（v2.4.3）
        
        Args:
            truth_table: 真偽表データ
            parsed_data: 解析済みデータ
            source_code: 元のソースコード全体
        
        Returns:
            str: スタンドアロンテストコード（元のソース + テストコード）
        """
        self.logger.info("v2.4.3: スタンドアロン版テストコードの生成を開始")
        
        # v4.3.4.1: 外部関数のプロトタイプ宣言をstaticに変換
        modified_source = self._convert_external_prototypes_to_static(
            source_code, parsed_data.external_functions
        )
        
        # v4.4: テスト対象関数をstaticに変換
        modified_source = self._convert_target_function_to_static(
            modified_source, parsed_data.function_name
        )
        
        # v4.8.7: main関数と対象外関数を除外
        modified_source = self._remove_non_target_functions(
            modified_source, parsed_data.function_name
        )
        
        # 元のソースコードをベースにする
        parts = [modified_source]
        
        # 区切り線を追加
        parts.append("\n\n" + "//" + "=" * 78)
        parts.append("// 以下、自動生成されたテストコード")
        parts.append("//" + "=" * 78 + "\n")
        
        # Unity framework のインクルード
        parts.append('#include "unity.h"')
        
        # モック変数とモック関数
        mock_code = self.mock_gen.generate_mocks(parsed_data)
        if mock_code:
            parts.append("\n// ===== モック変数とモック関数 =====")
            parts.append(mock_code)
        
        # テスト関数群
        test_functions = self._generate_all_test_functions(truth_table, parsed_data)
        if test_functions:
            parts.append("\n// ===== テスト関数群 =====")
            parts.append(test_functions)
        
        # setUp/tearDown (v5.0.0: static/global変数初期化追加)
        setup_teardown = self._generate_setup_teardown(parsed_data)
        if setup_teardown:
            parts.append("\n// ===== setUp/tearDown =====")
            parts.append(setup_teardown)
        
        # main関数
        main_function = self._generate_main_function(truth_table, parsed_data)
        if main_function:
            parts.append("\n// ===== main関数 =====")
            parts.append(main_function)
        
        result = '\n'.join(parts)
        
        self.logger.info(f"✓ v2.4.3: スタンドアロン版テストコード生成完了")
        
        return result
    
    def _convert_external_prototypes_to_static(self, source_code: str, 
                                                external_functions: list) -> str:
        """
        外部関数のプロトタイプ宣言をstaticに変換（v4.3.4.1）
        
        モック関数と同じシグネチャにするため、元のプロトタイプ宣言にstaticを追加
        
        Args:
            source_code: 元のソースコード
            external_functions: 外部関数名のリスト
        
        Returns:
            変換後のソースコード
        """
        import re
        
        if not external_functions:
            return source_code
        
        modified = source_code
        
        for func_name in external_functions:
            # プロトタイプ宣言のパターン: 戻り値型 関数名(...);
            # static がまだ付いていないものを対象
            # 例: void Utf18(const Utx174 Utx40);
            #     uint8_t Utf8(void);
            pattern = rf'^(\s*)((?:(?:const\s+)?(?:unsigned\s+|signed\s+)?(?:\w+)(?:\s*\*)?)\s+)({re.escape(func_name)})\s*\(([^)]*)\)\s*;'
            
            def add_static(match):
                indent = match.group(1)
                return_type = match.group(2)
                name = match.group(3)
                params = match.group(4)
                # すでにstaticが付いていないか確認
                if 'static' in return_type:
                    return match.group(0)
                return f'{indent}static {return_type}{name}({params});'
            
            modified = re.sub(pattern, add_static, modified, flags=re.MULTILINE)
        
        return modified
    
    def _convert_target_function_to_static(self, source_code: str, function_name: str) -> str:
        """
        テスト対象関数をstaticに変換（v4.4）
        
        テスト対象関数の定義とプロトタイプ宣言の両方にstaticを追加する
        
        Args:
            source_code: 元のソースコード
            function_name: テスト対象関数名
        
        Returns:
            変換後のソースコード
        """
        import re
        
        if not function_name:
            return source_code
        
        modified = source_code
        
        # パターン1: 関数定義 (戻り値型 関数名(...) {)
        # 例: void Utf1(void) {
        #     uint8_t myFunc(int a, int b) {
        func_def_pattern = rf'^(\s*)((?:(?:const\s+)?(?:unsigned\s+|signed\s+)?(?:\w+)(?:\s*\*)*)\s+)({re.escape(function_name)})\s*\(([^)]*)\)\s*{{'
        
        def add_static_to_def(match):
            indent = match.group(1)
            return_type = match.group(2)
            name = match.group(3)
            params = match.group(4)
            # すでにstaticが付いていないか確認
            if 'static' in return_type:
                return match.group(0)
            self.logger.info(f"v4.4: 関数定義 {name} にstaticを追加")
            return f'{indent}static {return_type}{name}({params}) {{'
        
        modified = re.sub(func_def_pattern, add_static_to_def, modified, flags=re.MULTILINE)
        
        # パターン2: プロトタイプ宣言 (戻り値型 関数名(...);)
        # 例: void Utf1(void);
        #     uint8_t myFunc(int a, int b);
        proto_pattern = rf'^(\s*)((?:(?:const\s+)?(?:unsigned\s+|signed\s+)?(?:\w+)(?:\s*\*)*)\s+)({re.escape(function_name)})\s*\(([^)]*)\)\s*;'
        
        def add_static_to_proto(match):
            indent = match.group(1)
            return_type = match.group(2)
            name = match.group(3)
            params = match.group(4)
            # すでにstaticが付いていないか確認
            if 'static' in return_type:
                return match.group(0)
            self.logger.info(f"v4.4: プロトタイプ宣言 {name} にstaticを追加")
            return f'{indent}static {return_type}{name}({params});'
        
        modified = re.sub(proto_pattern, add_static_to_proto, modified, flags=re.MULTILINE)
        
        return modified
    
    def _remove_non_target_functions(self, source_code: str, target_function_name: str) -> str:
        """
        main関数およびテスト対象以外の関数定義を除外（v4.8.7）
        
        テスト対象関数、型定義、マクロ、グローバル変数は保持し、
        それ以外の関数定義（特にmain関数）を除去する
        
        Args:
            source_code: 元のソースコード
            target_function_name: テスト対象関数名
        
        Returns:
            対象外関数を除外したソースコード
        """
        import re
        
        if not target_function_name:
            return source_code
        
        # 関数定義を検出するパターン
        # 戻り値型 関数名(パラメータ) { ... }
        # 注意: 波括弧のネストを正しく処理する必要がある
        
        lines = source_code.split('\n')
        result_lines = []
        
        in_function = False
        current_function_name = None
        brace_count = 0
        function_start_line = 0
        
        # 関数定義の開始を検出するパターン
        # static, extern, inline などの修飾子にも対応
        func_start_pattern = re.compile(
            r'^(\s*)(static\s+|extern\s+|inline\s+)*((?:const\s+)?(?:unsigned\s+|signed\s+)?(?:volatile\s+)?(?:\w+)(?:\s*\*)*)\s+(\w+)\s*\([^)]*\)\s*{'
        )
        # プロトタイプ宣言（関数定義ではない）を検出
        proto_pattern = re.compile(
            r'^(\s*)(static\s+|extern\s+|inline\s+)*((?:const\s+)?(?:unsigned\s+|signed\s+)?(?:volatile\s+)?(?:\w+)(?:\s*\*)*)\s+(\w+)\s*\([^)]*\)\s*;'
        )
        
        i = 0
        while i < len(lines):
            line = lines[i]
            
            if not in_function:
                # 関数定義の開始を検出
                match = func_start_pattern.match(line)
                if match:
                    current_function_name = match.group(4)
                    
                    # テスト対象関数の場合は保持
                    if current_function_name == target_function_name:
                        result_lines.append(line)
                        if '{' in line:
                            brace_count = line.count('{') - line.count('}')
                            if brace_count > 0:
                                in_function = True
                        i += 1
                        continue
                    
                    # main関数またはその他の関数は除外
                    self.logger.info(f"v4.8.7: 対象外関数 '{current_function_name}' を除外")
                    
                    # 関数の終わりまでスキップ
                    brace_count = line.count('{') - line.count('}')
                    if brace_count == 0:
                        # 同じ行で関数が完結している場合（インライン関数など）
                        i += 1
                        continue
                    
                    # 関数の終わりを探す
                    i += 1
                    while i < len(lines) and brace_count > 0:
                        brace_count += lines[i].count('{') - lines[i].count('}')
                        i += 1
                    continue
                else:
                    # 関数定義以外の行は保持
                    result_lines.append(line)
            else:
                # 関数内の処理
                result_lines.append(line)
                brace_count += line.count('{') - line.count('}')
                if brace_count == 0:
                    in_function = False
                    current_function_name = None
            
            i += 1
        
        return '\n'.join(result_lines)
    
    def _generate_header(self, parsed_data: ParsedData) -> str:
        """
        ヘッダーコメントを生成
        
        Args:
            parsed_data: 解析済みデータ
        
        Returns:
            ヘッダーコメント
        """
        lines = []
        lines.append("/*")
        lines.append(f" * test_{parsed_data.function_name}_mcdc.c")
        lines.append(f" * {parsed_data.function_name}関数のMC/DC 100%カバレッジ単体テスト")
        lines.append(" *")
        lines.append(" * このファイルは自動生成されました")
        lines.append(" * MC/DC (Modified Condition/Decision Coverage) 100%達成を目的としたテスト")
        lines.append(" */")
        
        return '\n'.join(lines)
    
    def _generate_includes(self) -> str:
        """
        #include文を生成
        
        Returns:
            #include文
        """
        lines = []
        lines.append("#include \"unity.h\"")
        lines.append("#include <stdint.h>")
        lines.append("#include <stdbool.h>")
        lines.append("#include <string.h>")
        lines.append("#include <limits.h>")
        
        return '\n'.join(lines)
    
    def _generate_type_definitions(self, parsed_data: ParsedData = None) -> str:
        """
        型定義を生成
        
        Args:
            parsed_data: 解析済みデータ（v2.2: 型定義・変数宣言の自動生成用）
        
        Returns:
            型定義
        """
        lines = []
        
        # v2.4.2: マクロ定義を先頭に追加
        if parsed_data and parsed_data.macro_definitions:
            lines.append("// ===== マクロ定義 =====")
            for macro_def in parsed_data.macro_definitions:
                lines.append(macro_def)
            lines.append("")
        
        # v2.2: テスト対象関数のプロトタイプ宣言
        lines.append("// ===== テスト対象関数のプロトタイプ宣言 =====")
        if parsed_data and parsed_data.function_info:
            func_info = parsed_data.function_info
            params = []
            if func_info.parameters:
                for param in func_info.parameters:
                    param_type = param.get('type', 'int')
                    param_name = param.get('name', '')
                    params.append(f"{param_type} {param_name}")
            param_str = ', '.join(params) if params else 'void'
            lines.append(f"extern {func_info.return_type} {func_info.name}({param_str});")
        elif parsed_data and parsed_data.function_name:
            # function_infoがない場合でも、関数名があればプロトタイプを生成
            lines.append(f"extern void {parsed_data.function_name}(void);")
            lines.append(f"// 注意: 関数情報が不完全なため、戻り値と引数を手動で修正してください")
        else:
            lines.append("// extern void target_function(void);")
            lines.append("// 警告: テスト対象関数の情報が取得できませんでした")
        lines.append("")
        
        # v2.2: 型定義の自動生成
        lines.append("// ===== テスト対象関数で使用される型定義 =====")
        if parsed_data and parsed_data.typedefs:
            # 依存関係を解決してソート
            from src.parser.dependency_resolver import DependencyResolver
            resolver = DependencyResolver()
            sorted_typedefs = resolver.resolve_order(parsed_data.typedefs)
            
            self.logger.info(f"型定義を {len(sorted_typedefs)} 個生成します")
            for typedef in sorted_typedefs:
                lines.append(typedef.definition)
                lines.append("")
        else:
            lines.append("// 型定義が検出されませんでした")
            lines.append("// 必要に応じて元のソースから手動でコピーしてください")
            lines.append("")
        
        # v2.2: 変数宣言の自動生成
        lines.append("// ===== 外部変数（テスト対象関数で使用） =====")
        if parsed_data and parsed_data.variables:
            extern_vars = [var for var in parsed_data.variables if var.is_extern]
            if extern_vars:
                self.logger.info(f"外部変数を {len(extern_vars)} 個生成します")
                for var in extern_vars:
                    lines.append(var.definition)
            else:
                lines.append("// 外部変数が検出されませんでした")
        else:
            lines.append("// 外部変数が検出されませんでした")
        lines.append("")
        
        # v4.7: 関数ポインタテーブルの定義を追加
        if parsed_data and parsed_data.function_pointer_tables:
            lines.append("// ===== 関数ポインタテーブル =====")
            for table in parsed_data.function_pointer_tables:
                lines.append(f"/* 関数ポインタテーブル: {table.name} ({table.size}個の関数) */")
                lines.append(table.format_definition())
                lines.append("")
            self.logger.info(f"関数ポインタテーブルを {len(parsed_data.function_pointer_tables)} 個生成しました")
        
        return '\n'.join(lines)
    
    def _generate_all_test_functions(self, truth_table: TruthTableData, parsed_data: ParsedData) -> str:
        """
        全てのテスト関数を生成
        
        Args:
            truth_table: 真偽表データ
            parsed_data: 解析済みデータ
        
        Returns:
            テスト関数群
        """
        lines = []
        lines.append("// ===== テスト関数 =====")
        lines.append("")
        
        # テストケースサマリー
        summary = self.comment_gen.generate_test_summary(truth_table.test_cases)
        lines.append(summary)
        lines.append("")
        
        # 各テスト関数を生成（プロトタイプ宣言 + 本体）
        for test_case in truth_table.test_cases:
            # テスト関数名を生成
            func_name = self.test_func_gen._generate_test_name(test_case, parsed_data)
            
            # プロトタイプ宣言を追加
            lines.append(f"// プロトタイプ宣言")
            lines.append(f"void {func_name}(void);")
            lines.append("")
            
            # テスト関数本体を生成
            test_func = self.test_func_gen.generate_test_function(test_case, parsed_data)
            lines.append(test_func)
            lines.append("")
        
        return '\n'.join(lines)
    
    def _generate_setup_teardown(self, parsed_data: ParsedData = None) -> str:
        """
        setUp/tearDown関数を生成 (v5.0.0: static/global変数初期化追加, v5.0.2: 関数分離)
        
        Args:
            parsed_data: 解析済みデータ（v5.0.0で追加）
        
        Returns:
            setUp/tearDown関数
        """
        lines = []
        
        # v5.0.2: reset_all_global_values関数を生成
        init_code = []
        if parsed_data:
            init_code = self._generate_variable_init_code(parsed_data)
        
        lines.append("// ===== グローバル変数リセット関数 =====")
        lines.append("")
        lines.append("/**")
        lines.append(" * 全てのstatic変数・グローバル変数をリセット")
        lines.append(" */")
        lines.append("static void reset_all_global_values(void) {")
        if init_code:
            for line in init_code:
                lines.append(f"    {line}")
        else:
            lines.append("    // 初期化対象の変数なし")
        lines.append("}")
        lines.append("")
        
        lines.append("// ===== setUp/tearDown =====")
        lines.append("")
        lines.append("/**")
        lines.append(" * 各テストの前に実行")
        lines.append(" */")
        lines.append("void setUp(void) {")
        lines.append("    // モックをリセット")
        lines.append("    reset_all_mocks();")
        lines.append("")
        lines.append("    // グローバル変数をリセット")
        lines.append("    reset_all_global_values();")
        lines.append("}")
        lines.append("")
        lines.append("/**")
        lines.append(" * 各テストの後に実行")
        lines.append(" */")
        lines.append("void tearDown(void) {")
        lines.append("    // クリーンアップ処理")
        lines.append("}")
        
        return '\n'.join(lines)
        
        return '\n'.join(lines)
    
    def _generate_variable_init_code(self, parsed_data: ParsedData) -> list:
        """
        static変数とグローバル変数の初期化コードを生成 (v5.0.4: 全関数パラメータ除外)
        
        Args:
            parsed_data: 解析済みデータ
        
        Returns:
            初期化コード行のリスト
        """
        init_lines = []
        
        # v5.0.4: 全関数のパラメータ名を収集（これらは除外対象）
        param_names = set()
        if hasattr(parsed_data, 'function_signatures') and parsed_data.function_signatures:
            for func_name, sig in parsed_data.function_signatures.items():
                # sigがオブジェクト形式の場合
                if hasattr(sig, 'parameters'):
                    for param in sig.parameters:
                        # パラメータが辞書形式の場合
                        if isinstance(param, dict) and 'name' in param:
                            param_names.add(param['name'])
                        # パラメータがオブジェクト形式の場合
                        elif hasattr(param, 'name') and param.name:
                            param_names.add(param.name)
                        # パラメータが文字列形式の場合 ("型 名前")
                        elif isinstance(param, str):
                            parts = param.split()
                            if parts:
                                param_names.add(parts[-1].replace('*', ''))
        
        # function_infoからもパラメータ名を収集（テスト対象関数）
        if hasattr(parsed_data, 'function_info') and parsed_data.function_info:
            if hasattr(parsed_data.function_info, 'parameters'):
                for param in parsed_data.function_info.parameters:
                    if isinstance(param, dict) and 'name' in param:
                        param_names.add(param['name'])
                    elif hasattr(param, 'name') and param.name:
                        param_names.add(param.name)
                    elif isinstance(param, str):
                        parts = param.split()
                        if parts:
                            param_names.add(parts[-1].replace('*', ''))
        
        # v5.0.3: ローカル変数名を収集（これらも除外対象）
        local_var_names = set()
        if hasattr(parsed_data, 'local_variables') and parsed_data.local_variables:
            local_var_names = set(parsed_data.local_variables.keys())
        
        # static変数の初期化
        if hasattr(parsed_data, 'static_variables') and parsed_data.static_variables:
            for var in parsed_data.static_variables:
                # パラメータやローカル変数は除外
                if var.name in param_names or var.name in local_var_names:
                    continue
                init_line = self._generate_single_var_init(var, parsed_data)
                if init_line:
                    init_lines.append(init_line)
        
        # グローバル変数の初期化
        if hasattr(parsed_data, 'global_variable_infos') and parsed_data.global_variable_infos:
            for var in parsed_data.global_variable_infos:
                # パラメータやローカル変数は除外
                if var.name in param_names or var.name in local_var_names:
                    continue
                init_line = self._generate_single_var_init(var, parsed_data)
                if init_line:
                    init_lines.append(init_line)
        
        # 従来のglobal_variables（名前のみ）も処理
        # ただし、static_variablesとglobal_variable_infosで処理済みの場合は除外
        if hasattr(parsed_data, 'global_variables') and parsed_data.global_variables:
            # 既に処理済みの変数名を収集
            processed_names = set()
            if hasattr(parsed_data, 'global_variable_infos'):
                processed_names = {v.name for v in parsed_data.global_variable_infos}
            if hasattr(parsed_data, 'static_variables'):
                processed_names |= {v.name for v in parsed_data.static_variables}
            
            # 構造体のメンバー名を収集（これらは除外）
            struct_member_names = set()
            if hasattr(parsed_data, 'struct_definitions'):
                for struct_def in parsed_data.struct_definitions:
                    if hasattr(struct_def, 'members'):
                        for member in struct_def.members:
                            if hasattr(member, 'name'):
                                struct_member_names.add(member.name)
            
            for var_name in parsed_data.global_variables:
                # 既に処理済み、構造体メンバー、パラメータ、ローカル変数の場合は除外
                if var_name in processed_names:
                    continue
                if var_name in struct_member_names:
                    continue
                if var_name in param_names:
                    continue
                if var_name in local_var_names:
                    continue
                # 型情報がない場合は0で初期化
                init_lines.append(f"{var_name} = 0;")
        
        return init_lines
    
    def _generate_single_var_init(self, var, parsed_data: ParsedData) -> str:
        """
        単一変数の初期化コードを生成 (v5.0.0, v5.0.2: extern変数も初期化)
        
        Args:
            var: VariableDeclInfo
            parsed_data: 解析済みデータ
        
        Returns:
            初期化コード行
        """
        var_name = var.name
        var_type = var.var_type
        
        # v5.0.2: extern変数も初期化対象に含める（コメントで明示）
        # extern変数は他のモジュールで定義されているが、テスト時はリセットする
        
        # 配列の場合
        if var.is_array:
            if var.array_size and var.array_size > 0:
                return f"memset({var_name}, 0, sizeof({var_name}));"
            else:
                return f"memset({var_name}, 0, sizeof({var_name}));"
        
        # 構造体の場合
        if var.is_struct or self._is_struct_type(var_type, parsed_data):
            return f"memset(&{var_name}, 0, sizeof({var_name}));"
        
        # ポインタの場合
        if '*' in var_type:
            return f"{var_name} = NULL;"
        
        # 基本型の場合
        if self._is_integer_type(var_type):
            return f"{var_name} = 0;"
        elif self._is_float_type(var_type):
            return f"{var_name} = 0.0;"
        elif 'char' in var_type.lower():
            return f"{var_name} = '\\0';"
        else:
            # 不明な型は0で初期化
            return f"{var_name} = 0;"
    
    def _is_struct_type(self, var_type: str, parsed_data: ParsedData) -> bool:
        """
        型名が構造体かどうか判定 (v5.0.0)
        
        Args:
            var_type: 型名
            parsed_data: 解析済みデータ
        
        Returns:
            構造体ならTrue
        """
        if 'struct' in var_type:
            return True
        
        # typedef された構造体名をチェック
        clean_type = var_type.replace('*', '').replace('const', '').strip()
        
        # struct_definitionsからチェック
        if hasattr(parsed_data, 'struct_definitions'):
            for struct_def in parsed_data.struct_definitions:
                if struct_def.name == clean_type or struct_def.original_name == clean_type:
                    return True
        
        # typedefsからチェック
        if hasattr(parsed_data, 'typedefs'):
            for typedef in parsed_data.typedefs:
                if hasattr(typedef, 'name') and typedef.name == clean_type:
                    if hasattr(typedef, 'original_type') and 'struct' in str(typedef.original_type):
                        return True
        
        return False
    
    def _is_integer_type(self, var_type: str) -> bool:
        """整数型かどうか判定"""
        int_types = [
            'int', 'short', 'long', 'char',
            'uint8_t', 'uint16_t', 'uint32_t', 'uint64_t',
            'int8_t', 'int16_t', 'int32_t', 'int64_t',
            'size_t', 'ssize_t', 'ptrdiff_t',
            'unsigned', 'signed',
            'BYTE', 'WORD', 'DWORD', 'BOOL',
            # 組込み系でよく使われる型
            'U8', 'U16', 'U32', 'U64',
            'S8', 'S16', 'S32', 'S64',
        ]
        clean_type = var_type.replace('unsigned', '').replace('signed', '').strip()
        for itype in int_types:
            if itype in clean_type:
                return True
        return False
    
    def _is_float_type(self, var_type: str) -> bool:
        """浮動小数点型かどうか判定"""
        float_types = ['float', 'double', 'long double']
        for ftype in float_types:
            if ftype in var_type:
                return True
        return False
        
        return '\n'.join(lines)
    
    def _extract_target_function(self, source_code: str, function_name: str) -> Optional[str]:
        """
        テスト対象関数の本体を抽出（v2.2の新機能）
        
        Args:
            source_code: 元のソースコード
            function_name: 対象関数名
            
        Returns:
            抽出されたコードセクション
        """
        try:
            # 関数本体のみを抽出（依存関係は今回は含めない）
            extracted = self.code_extractor.extract_function_only(source_code, function_name)
            
            if extracted and extracted.has_content():
                return extracted.to_code_section()
            
            return None
            
        except Exception as e:
            self.logger.error(f"関数抽出中にエラーが発生: {e}")
            return None
    
    def _generate_main_function(self, truth_table: TruthTableData, parsed_data: ParsedData) -> str:
        """
        main関数を生成（v2.3の新機能）
        
        Args:
            truth_table: 真偽表データ
            parsed_data: 解析済みデータ
            
        Returns:
            main関数のコード
        """
        lines = []
        lines.append("// ===== main関数 =====")
        lines.append("")
        lines.append("/**")
        lines.append(" * テストスイートのエントリーポイント")
        lines.append(" */")
        lines.append("int main(void) {")
        lines.append("    UNITY_BEGIN();")
        lines.append("    ")
        
        # ヘッダー情報
        lines.append("    printf(\"==============================================\\n\");")
        lines.append(f"    printf(\"{parsed_data.function_name} Function MC/DC 100%% Coverage Test Suite\\n\");")
        lines.append("    printf(\"==============================================\\n\");")
        lines.append("    printf(\"Target: MC/DC (Modified Condition/Decision Coverage) 100%%\\n\");")
        lines.append(f"    printf(\"Total Test Cases: {truth_table.total_tests}\\n\");")
        lines.append("    printf(\"==============================================\\n\\n\");")
        lines.append("    ")
        
        # 条件の種類別にテストケースをグループ化
        grouped_tests = self._group_test_cases_by_condition(truth_table.test_cases)
        
        # グループごとにRUN_TESTを生成
        for group_idx, (condition_desc, test_cases) in enumerate(grouped_tests, 1):
            if group_idx > 1:
                lines.append("    ")
            
            # グループのヘッダー
            start_no = test_cases[0].no
            end_no = test_cases[-1].no
            lines.append(f"    printf(\"--- {condition_desc} (No.{start_no}-{end_no}) ---\\n\");")
            
            # 各テストケースのRUN_TEST
            for test_case in test_cases:
                func_name = self.test_func_gen._generate_test_name(test_case, parsed_data)
                lines.append(f"    RUN_TEST({func_name});")
        
        lines.append("    ")
        lines.append("    return UNITY_END();")
        lines.append("}")
        
        return '\n'.join(lines)
    
    def _group_test_cases_by_condition(self, test_cases: List[TestCase]) -> List[tuple]:
        """
        テストケースを条件別にグループ化
        
        Args:
            test_cases: テストケースのリスト
            
        Returns:
            (条件の説明, テストケースのリスト)のタプルのリスト
        """
        if not test_cases:
            return []
        
        groups = []
        current_condition = None
        current_group = []
        
        for test_case in test_cases:
            # 条件を簡略化（長すぎる場合は切り詰め）
            condition = test_case.condition
            if len(condition) > 50:
                condition = condition[:47] + "..."
            
            if current_condition is None:
                current_condition = condition
                current_group = [test_case]
            elif current_condition == condition:
                current_group.append(test_case)
            else:
                # グループを保存
                groups.append((self._get_condition_description(current_condition), current_group))
                # 新しいグループを開始
                current_condition = condition
                current_group = [test_case]
        
        # 最後のグループを保存
        if current_group:
            groups.append((self._get_condition_description(current_condition), current_group))
        
        return groups
    
    def _get_condition_description(self, condition: str) -> str:
        """
        条件の説明を生成
        
        Args:
            condition: 条件式
            
        Returns:
            説明文
        """
        # "if (...)" や "switch (...)" から条件部分を抽出
        if "if" in condition:
            return "Condition Tests"
        elif "switch" in condition:
            return "Switch Case Tests"
        else:
            return "Tests"


if __name__ == "__main__":
    # UnityTestGeneratorのテスト
    print("=" * 70)
    print("UnityTestGenerator のテスト")
    print("=" * 70)
    print()
    
    from src.data_structures import ParsedData, TruthTableData, TestCase, Condition, ConditionType
    
    # テスト用データ
    parsed_data = ParsedData(
        file_name="test.c",
        function_name="test_func",
        external_functions=['f4', 'mx27'],
        global_variables=['v9', 'mx63', 'v10']
    )
    
    # 条件を追加
    parsed_data.conditions.append(
        Condition(
            line=10,
            type=ConditionType.SIMPLE_IF,
            expression="(v10 > 30)"
        )
    )
    
    truth_table = TruthTableData(
        function_name="test_func",
        test_cases=[
            TestCase(no=1, truth="T", condition="if (v10 > 30)", expected="条件が真の処理を実行"),
            TestCase(no=2, truth="F", condition="if (v10 > 30)", expected="条件が偽の処理を実行"),
        ],
        total_tests=2
    )
    
    # Unityテストコードを生成
    generator = UnityTestGenerator()
    test_code = generator.generate(truth_table, parsed_data)
    
    # 生成されたコードを表示
    print("生成されたUnityテストコード:")
    print("=" * 70)
    full_code = test_code.to_string()
    
    # 最初の100行を表示
    lines = full_code.split('\n')
    for i, line in enumerate(lines[:100], 1):
        print(f"{i:3d}: {line}")
    
    if len(lines) > 100:
        print(f"\n... 他 {len(lines) - 100} 行")
    
    print()
    print("=" * 70)
    print(f"総行数: {len(lines)}行")
    print()
    
    # ファイルに保存
    output_file = "/tmp/test_generated_unity.c"
    test_code.save(output_file)
    print(f"✓ ファイルに保存: {output_file}")
    print()
    
    print("✓ UnityTestGeneratorが正常に動作しました")
