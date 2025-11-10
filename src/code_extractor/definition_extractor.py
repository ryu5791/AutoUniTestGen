"""
Definition Extractor Module

ソースコードから必要な定義（typedef、struct、union、define等）を抽出
"""

import re
from typing import List, Dict, Set, Tuple, Optional
from pathlib import Path
import logging

class DefinitionExtractor:
    """ソースコードから定義を抽出するクラス"""
    
    def __init__(self):
        """初期化"""
        self.logger = logging.getLogger(__name__)
        
    def extract_all_definitions(self, source_code: str) -> Dict[str, List[str]]:
        """
        すべての定義を抽出
        
        Args:
            source_code: ソースコード
            
        Returns:
            定義の辞書 {'defines': [...], 'typedefs': [...], 'structs': [...], 'unions': [...], 'enums': [...]}
        """
        definitions = {
            'defines': self.extract_defines(source_code),
            'typedefs': self.extract_typedefs(source_code),
            'structs': self.extract_structs(source_code),
            'unions': self.extract_unions(source_code),
            'enums': self.extract_enums(source_code),
            'global_vars': self.extract_global_variables(source_code)
        }
        
        return definitions
    
    def extract_defines(self, source_code: str) -> List[str]:
        """
        #define定義を抽出
        
        Args:
            source_code: ソースコード
            
        Returns:
            #define定義のリスト
        """
        defines = []
        # 複数行にまたがるdefineも考慮
        pattern = r'#define\s+\w+(?:\([^)]*\))?\s+[^\n\\]+(?:\\\n[^\n\\]+)*'
        
        for match in re.finditer(pattern, source_code):
            define_text = match.group(0)
            # バックスラッシュと改行を適切に処理
            define_text = define_text.replace('\\\n', ' \\\n    ')
            defines.append(define_text)
        
        return defines
    
    def extract_typedefs(self, source_code: str) -> List[str]:
        """
        typedef定義を抽出（struct/union/enumを含む）
        
        Args:
            source_code: ソースコード
            
        Returns:
            typedef定義のリスト
        """
        typedefs = []
        
        # typedef struct/union/enum { ... } name; の形式
        pattern = r'typedef\s+(?:struct|union|enum)(?:\s+\w+)?\s*\{[^}]+\}\s*\w+\s*;'
        
        for match in re.finditer(pattern, source_code, re.DOTALL):
            typedef_text = match.group(0)
            typedefs.append(typedef_text)
        
        # typedef 既存型 新型; の形式
        simple_pattern = r'typedef\s+(?!struct|union|enum)[^;]+;'
        
        for match in re.finditer(simple_pattern, source_code):
            typedef_text = match.group(0)
            # 複雑なtypedefは既に処理済みなので除外
            if '{' not in typedef_text:
                typedefs.append(typedef_text)
        
        return typedefs
    
    def extract_structs(self, source_code: str) -> List[str]:
        """
        struct定義を抽出（typedefでないもの）
        
        Args:
            source_code: ソースコード
            
        Returns:
            struct定義のリスト
        """
        structs = []
        
        # typedef以外のstruct定義
        pattern = r'(?<!typedef\s)struct\s+\w+\s*\{[^}]+\}\s*(?:\w+\s*(?:,\s*\w+)*)?;'
        
        for match in re.finditer(pattern, source_code, re.DOTALL):
            struct_text = match.group(0)
            structs.append(struct_text)
        
        return structs
    
    def extract_unions(self, source_code: str) -> List[str]:
        """
        union定義を抽出（typedefでないもの）
        
        Args:
            source_code: ソースコード
            
        Returns:
            union定義のリスト
        """
        unions = []
        
        # typedef以外のunion定義
        pattern = r'(?<!typedef\s)union\s+\w+\s*\{[^}]+\}\s*(?:\w+\s*(?:,\s*\w+)*)?;'
        
        for match in re.finditer(pattern, source_code, re.DOTALL):
            union_text = match.group(0)
            unions.append(union_text)
        
        return unions
    
    def extract_enums(self, source_code: str) -> List[str]:
        """
        enum定義を抽出（typedefでないもの）
        
        Args:
            source_code: ソースコード
            
        Returns:
            enum定義のリスト
        """
        enums = []
        
        # typedef以外のenum定義
        pattern = r'(?<!typedef\s)enum\s+\w+\s*\{[^}]+\}\s*(?:\w+\s*(?:,\s*\w+)*)?;'
        
        for match in re.finditer(pattern, source_code, re.DOTALL):
            enum_text = match.group(0)
            enums.append(enum_text)
        
        return enums
    
    def extract_global_variables(self, source_code: str) -> List[str]:
        """
        グローバル変数宣言を抽出
        
        Args:
            source_code: ソースコード
            
        Returns:
            グローバル変数宣言のリスト
        """
        global_vars = []
        
        # typedefとstructの定義を除去
        code_simplified = source_code
        
        # typedef struct/union/enum を除去
        code_simplified = re.sub(r'typedef\s+(?:struct|union|enum)(?:\s+\w+)?\s*\{[^}]+\}\s*\w+\s*;', '', code_simplified, flags=re.DOTALL)
        
        # 単独のstruct/union/enum定義を除去
        code_simplified = re.sub(r'(?:struct|union|enum)\s+\w+\s*\{[^}]+\}\s*(?:\w+\s*(?:,\s*\w+)*)?;', '', code_simplified, flags=re.DOTALL)
        
        # 関数定義を除去
        code_simplified = self._remove_function_bodies(code_simplified)
        
        # グローバル変数を探す（ユーザー定義型も考慮）
        lines = code_simplified.split('\n')
        
        for line in lines:
            line = line.strip()
            
            # 空行、コメント、プリプロセッサ指令をスキップ
            if not line or line.startswith('//') or line.startswith('#') or line.startswith('/*'):
                continue
            
            # typedefをスキップ
            if line.startswith('typedef'):
                continue
            
            # 変数宣言のパターン
            # 型名 変数名; または 型名 変数名 = 値;
            # externも含む
            if ';' in line:
                # 関数プロトタイプを除外
                if '(' in line and ')' in line:
                    continue
                
                # 基本的な変数宣言パターン
                var_pattern = r'^(?:extern\s+)?(?:const\s+)?(?:static\s+)?(?:volatile\s+)?(\w+(?:\s*\*)*)\s+(\w+)(?:\[[^\]]*\])*(?:\s*=\s*[^;]+)?;'
                match = re.match(var_pattern, line)
                
                if match:
                    type_name = match.group(1).strip()
                    var_name = match.group(2).strip()
                    
                    # 有効な型名かチェック（基本型またはユーザー定義型）
                    valid_types = ['int', 'char', 'float', 'double', 'void', 
                                 'short', 'long', 'unsigned', 'signed',
                                 'uint8_t', 'uint16_t', 'uint32_t', 'uint64_t',
                                 'int8_t', 'int16_t', 'int32_t', 'int64_t',
                                 'size_t', 'bool', '_Bool',
                                 'Buffer', 'Data']  # ユーザー定義型も含む
                    
                    # 型名に有効な型が含まれているか、大文字で始まる型（ユーザー定義）か
                    if any(t in type_name for t in valid_types) or type_name[0].isupper():
                        global_vars.append(line)
        
        return global_vars
    
    def _remove_function_bodies(self, source_code: str) -> str:
        """
        関数本体を削除（グローバル変数抽出の前処理）
        
        Args:
            source_code: ソースコード
            
        Returns:
            関数本体を削除したコード
        """
        # 簡単な実装：{}のペアをカウントして関数本体を削除
        result = []
        brace_depth = 0
        in_function = False
        
        lines = source_code.split('\n')
        for line in lines:
            # 関数定義の開始を検出（簡易的）
            if '{' in line and brace_depth == 0 and '(' in line and ')' in line:
                in_function = True
            
            if not in_function:
                result.append(line)
            
            # ブレースカウント
            for char in line:
                if char == '{':
                    brace_depth += 1
                elif char == '}':
                    brace_depth -= 1
                    if brace_depth == 0:
                        in_function = False
        
        return '\n'.join(result)
    
    def extract_dependencies(self, definitions: Dict[str, List[str]]) -> List[str]:
        """
        依存関係を考慮して定義を順序付け
        
        Args:
            definitions: 定義の辞書
            
        Returns:
            順序付けされた定義のリスト
        """
        ordered = []
        
        # 1. #defineは最初
        ordered.extend(definitions.get('defines', []))
        
        # 2. typedef（依存関係を考慮）
        ordered.extend(self._order_typedefs(definitions.get('typedefs', [])))
        
        # 3. struct/union/enum
        ordered.extend(definitions.get('structs', []))
        ordered.extend(definitions.get('unions', []))
        ordered.extend(definitions.get('enums', []))
        
        # 4. グローバル変数
        ordered.extend(definitions.get('global_vars', []))
        
        return ordered
    
    def _order_typedefs(self, typedefs: List[str]) -> List[str]:
        """
        typedef定義を依存関係順に並べる
        
        Args:
            typedefs: typedef定義のリスト
            
        Returns:
            順序付けされたtypedef定義のリスト
        """
        # 簡単な実装：定義された型名を抽出して依存関係をチェック
        typedef_dict = {}
        typedef_names = []
        
        for typedef in typedefs:
            # typedef ... name; から名前を抽出
            match = re.search(r'}\s*(\w+)\s*;', typedef)
            if match:
                name = match.group(1)
                typedef_dict[name] = typedef
                typedef_names.append(name)
        
        # 依存関係を考慮した順序付け（簡易版）
        ordered = []
        processed = set()
        
        def add_typedef(name):
            if name in processed:
                return
            typedef = typedef_dict.get(name, '')
            # 他の型への参照をチェック
            for other_name in typedef_names:
                if other_name != name and other_name in typedef:
                    add_typedef(other_name)
            if name not in processed:
                ordered.append(typedef_dict[name])
                processed.add(name)
        
        for name in typedef_names:
            add_typedef(name)
        
        return ordered
    
    def generate_test_definitions(self, source_code: str, target_function: str) -> str:
        """
        テストコード用の定義セクションを生成
        
        Args:
            source_code: ソースコード
            target_function: テスト対象関数名
            
        Returns:
            テストコード用の定義セクション
        """
        definitions = self.extract_all_definitions(source_code)
        ordered_defs = self.extract_dependencies(definitions)
        
        lines = []
        lines.append("// ===== ソースコードから抽出された定義 =====")
        lines.append("")
        
        if definitions['defines']:
            lines.append("// マクロ定義")
            for define in definitions['defines']:
                lines.append(define)
            lines.append("")
        
        if definitions['typedefs']:
            lines.append("// 型定義")
            for typedef in self._order_typedefs(definitions['typedefs']):
                lines.append(typedef)
            lines.append("")
        
        if definitions['structs'] or definitions['unions'] or definitions['enums']:
            lines.append("// 構造体・共用体・列挙型")
            for item in definitions['structs'] + definitions['unions'] + definitions['enums']:
                lines.append(item)
            lines.append("")
        
        if definitions['global_vars']:
            lines.append("// グローバル変数宣言")
            for var in definitions['global_vars']:
                # extern宣言は実体定義に変更
                if 'extern' in var:
                    var = var.replace('extern ', '')
                lines.append(var)
            lines.append("")
        
        lines.append("// ===== テスト対象関数のプロトタイプ =====")
        lines.append(f"void {target_function}(void);")
        lines.append("")
        
        return '\n'.join(lines)


if __name__ == "__main__":
    # テスト
    sample_code = """
#include <stdint.h>

#define MAX_SIZE 100
#define MIN_SIZE 10

typedef struct {
    uint8_t data[MAX_SIZE];
    int size;
} Buffer;

typedef union {
    uint32_t value;
    uint8_t bytes[4];
} Data;

int global_count = 0;
extern int external_var;

void test_function() {
    // 関数本体
}
"""
    
    extractor = DefinitionExtractor()
    definitions = extractor.extract_all_definitions(sample_code)
    
    print("抽出された定義:")
    for key, values in definitions.items():
        if values:
            print(f"\n{key}:")
            for value in values:
                print(f"  {value}")
    
    print("\n" + "="*70)
    print("テストコード用定義セクション:")
    print("="*70)
    print(extractor.generate_test_definitions(sample_code, "test_function"))
