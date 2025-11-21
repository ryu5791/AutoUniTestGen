# AutoUniTestGen v2.7.1 次のチャットへの引継ぎ資料

**作成日**: 2025-11-20  
**現在のバージョン**: v2.7.1  
**状態**: ✅ **完成** - 構造体アサーション問題を修正済み

---

## ✅ v2.7.1で完了した作業

### 1. 構造体型判定機能の実装 ✅

**実装場所**: `src/test_generator/test_function_generator.py`

**追加メソッド**:
```python
def _is_struct_type(self, type_name: str) -> bool:
    """
    型が構造体かどうかを判定
    
    判定基準:
    1. _t で終わる（typedef struct の命名規則）
    2. 大文字で始まる（カスタム型の命名規則）
    3. 'struct' キーワードが含まれる
    
    Args:
        type_name: 型名
    
    Returns:
        構造体の場合True
    """
    if not type_name:
        return False
    
    # ポインタ記号を除去
    clean_type = type_name.replace('*', '').strip()
    
    # _t で終わる（typedef struct の命名規則）
    if clean_type.endswith('_t'):
        return True
    
    # 大文字で始まる（カスタム型）
    if clean_type and clean_type[0].isupper():
        return True
    
    # struct キーワードが含まれる
    if 'struct' in clean_type.lower():
        return True
    
    return False
```

### 2. アサーション生成ロジックの修正 ✅

**修正箇所**: `src/test_generator/test_function_generator.py` の `_generate_assertions()` メソッド

**Before (v2.6.6)**:
```python
def _generate_assertions(self, test_case: TestCase, parsed_data: ParsedData) -> str:
    lines = []
    lines.append("    // 結果を確認")
    
    # 戻り値のチェック（void以外の場合）
    if parsed_data.function_info and parsed_data.function_info.return_type != 'void':
        expected_value = self._calculate_expected_return_value(test_case, parsed_data)
        if expected_value is not None:
            lines.append(f"    TEST_ASSERT_EQUAL({expected_value}, result);")  # ← ❌ 構造体でエラー
```

**After (v2.7.1)**:
```python
def _generate_assertions(self, test_case: TestCase, parsed_data: ParsedData) -> str:
    lines = []
    lines.append("    // 結果を確認")
    lines.append("    // TODO: 期待値を設定してください")
    
    # 戻り値のチェック（void以外の場合）
    if parsed_data.function_info and parsed_data.function_info.return_type != 'void':
        return_type = parsed_data.function_info.return_type
        
        # 構造体型かチェック
        if self._is_struct_type(return_type):
            # 構造体の場合はTODOコメントで案内
            lines.append("    // 例: TEST_ASSERT_EQUAL(expected_value, result.member_name);")
        else:
            # 基本型の場合
            expected_value = self._calculate_expected_return_value(test_case, parsed_data)
            if expected_value is not None:
                lines.append(f"    TEST_ASSERT_EQUAL({expected_value}, result);")
```

### 3. UTF-8エンコーディング対応 ✅

**修正箇所**: `src/data_structures.py` の `TestCode.save()` メソッド

**Before**:
```python
def save(self, filepath: str) -> None:
    with open(filepath, 'w', encoding='shift_jis') as f:
        f.write(self.to_string())
```

**After**:
```python
def save(self, filepath: str) -> None:
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(self.to_string())
```

### 4. ドキュメント更新 ✅

以下のドキュメントをv2.7用に更新：
- `doc/design_class_diagram.md` - 構造体判定機能を追加
- `doc/design_sequence_diagram.md` - 構造体型アサーション生成フローを追加
- `RELEASE_NOTES_v2_7_1.md` - リリースノートを作成

### 5. テスト検証 ✅

**テストケース1: 構造体を返す関数**
```bash
python3 main.py -i /tmp/test_struct_return.c -f test_func -o /tmp/output_struct_test
```
✅ 結果: TODOコメントが正しく生成され、コンパイルエラーなし

**テストケース2: 基本型を返す関数**
```bash
python3 main.py -i /tmp/test_basic_return.c -f add -o /tmp/output_basic_test
```
✅ 結果: アサーションが正しく生成され、従来通りの動作を確認

---

## 🎯 次のバージョンで実装する機能

### v2.8.0の目標: 構造体メンバー情報の完全抽出

現在のv2.7.1では、構造体型を判定してTODOコメントを出力しています。
v2.8.0では、構造体の定義を解析してメンバー情報を取得し、メンバーごとのアサーションを自動生成します。

#### 実装計画

**Step 1: データ構造の拡張**

`src/data_structures.py` に以下を追加：
```python
@dataclass
class StructDefinition:
    """構造体定義"""
    name: str
    members: List[StructMember]
    is_typedef: bool
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'name': self.name,
            'members': [m.to_dict() for m in self.members],
            'is_typedef': self.is_typedef
        }

@dataclass
class StructMember:
    """構造体メンバー"""
    name: str
    type: str
    bit_width: Optional[int] = None
    is_pointer: bool = False
    is_array: bool = False
    array_size: Optional[int] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'name': self.name,
            'type': self.type,
            'bit_width': self.bit_width,
            'is_pointer': self.is_pointer,
            'is_array': self.is_array,
            'array_size': self.array_size
        }

@dataclass
class ParsedData:
    # 既存のフィールド
    function_info: FunctionInfo
    conditions: List[Condition]
    external_functions: List[str]
    typedefs: List[TypeDef]
    macros: List[Macro]
    variables: List[Variable]
    
    # v2.8で追加
    struct_definitions: List[StructDefinition] = field(default_factory=list)
```

**Step 2: 構造体定義の抽出**

`src/parser/typedef_extractor.py` に以下を追加：
```python
def extract_struct_definitions(self, ast) -> List[StructDefinition]:
    """
    ASTから構造体定義を抽出
    
    Args:
        ast: AST
    
    Returns:
        構造体定義のリスト
    """
    struct_defs = []
    
    for node in self._walk_ast(ast):
        if self._is_struct_definition(node):
            struct_def = self._parse_struct_node(node)
            if struct_def:
                struct_defs.append(struct_def)
    
    return struct_defs

def _parse_struct_node(self, node) -> Optional[StructDefinition]:
    """
    構造体ノードを解析
    
    Args:
        node: ASTノード
    
    Returns:
        StructDefinition
    """
    # 構造体名を取得
    struct_name = self._get_struct_name(node)
    
    # メンバーを抽出
    members = []
    for member_node in self._get_struct_members(node):
        member = self._parse_member_node(member_node)
        if member:
            members.append(member)
    
    # typedef かどうかを判定
    is_typedef = self._is_typedef_struct(node)
    
    return StructDefinition(
        name=struct_name,
        members=members,
        is_typedef=is_typedef
    )
```

**Step 3: TestFunctionGeneratorの拡張**

`src/test_generator/test_function_generator.py` に以下を追加：
```python
def _get_struct_members(
    self, 
    type_name: str, 
    parsed_data: ParsedData
) -> List[StructMember]:
    """
    構造体のメンバー情報を取得
    
    Args:
        type_name: 構造体の型名
        parsed_data: 解析済みデータ
    
    Returns:
        構造体メンバーのリスト
    """
    if not hasattr(parsed_data, 'struct_definitions'):
        return []
    
    # 型名をクリーンアップ
    clean_name = type_name.replace('*', '').strip()
    
    # 構造体定義を検索
    for struct_def in parsed_data.struct_definitions:
        if struct_def.name == clean_name:
            return struct_def.members
    
    return []

def _generate_assertions(self, test_case: TestCase, parsed_data: ParsedData) -> str:
    """
    アサーションコードを生成（v2.8で強化）
    
    Args:
        test_case: テストケース
        parsed_data: 解析済みデータ
    
    Returns:
        アサーションコード
    """
    lines = []
    lines.append("    // 結果を確認")
    lines.append("    // TODO: 期待値を設定してください")
    
    # 戻り値のチェック（void以外の場合）
    if parsed_data.function_info and parsed_data.function_info.return_type != 'void':
        return_type = parsed_data.function_info.return_type
        
        # 構造体型かチェック
        if self._is_struct_type(return_type):
            # 構造体のメンバー情報を取得
            members = self._get_struct_members(return_type, parsed_data)
            
            if members:
                # メンバーごとにアサーションを生成
                for member in members:
                    lines.append(f"    TEST_ASSERT_EQUAL(0, result.{member.name});")
            else:
                # メンバー情報が取得できない場合（v2.7.1と同じ）
                lines.append("    // 例: TEST_ASSERT_EQUAL(expected_value, result.member_name);")
        else:
            # 基本型の場合
            expected_value = self._calculate_expected_return_value(test_case, parsed_data)
            if expected_value is not None:
                lines.append(f"    TEST_ASSERT_EQUAL({expected_value}, result);")
    
    # ... 残りの処理
```

**Step 4: CCodeParserの統合**

`src/parser/c_code_parser.py` で構造体定義抽出を呼び出す：
```python
def parse(self, source_file: str, target_function: str = None) -> Optional[ParsedData]:
    # ... 既存の処理
    
    # 構造体定義を抽出（v2.8で追加）
    struct_definitions = []
    if ast:
        try:
            struct_definitions = self.typedef_extractor.extract_struct_definitions(ast)
            self.logger.info(f"{len(struct_definitions)}個の構造体定義を抽出しました")
        except Exception as e:
            self.logger.warning(f"構造体定義の抽出に失敗: {e}")
    
    # ParsedDataを作成
    parsed_data = ParsedData(
        function_name=target_function or "",
        function_info=function_info,
        conditions=conditions,
        external_functions=external_functions,
        typedefs=typedefs,
        macros=macros,
        variables=variables,
        struct_definitions=struct_definitions,  # v2.8で追加
        # ... その他のフィールド
    )
```

---

## 📋 実装のチェックリスト（v2.8.0用）

### データ構造
- [ ] `StructDefinition` データクラスを追加
- [ ] `StructMember` データクラスを追加
- [ ] `ParsedData` に `struct_definitions` フィールドを追加

### パーサー
- [ ] `TypedefExtractor.extract_struct_definitions()` を実装
- [ ] `TypedefExtractor._parse_struct_node()` を実装
- [ ] `TypedefExtractor._parse_member_node()` を実装
- [ ] `CCodeParser.parse()` で構造体定義抽出を呼び出し

### テスト生成
- [ ] `TestFunctionGenerator._get_struct_members()` を実装
- [ ] `TestFunctionGenerator._generate_assertions()` でメンバー情報を活用
- [ ] メンバーごとのアサーション生成ロジックを実装

### テスト
- [ ] 単純な構造体のテスト
- [ ] ネストした構造体のテスト
- [ ] ビットフィールドを含む構造体のテスト
- [ ] 配列メンバーを含む構造体のテスト
- [ ] ポインタメンバーを含む構造体のテスト

### ドキュメント
- [ ] クラス図を更新
- [ ] シーケンス図を更新
- [ ] リリースノートを作成
- [ ] 引継ぎ資料を作成

---

## 🧪 テスト計画（v2.8.0用）

### テストケース1: 単純な構造体

**入力**:
```c
typedef struct {
    uint8_t status;
    uint16_t value;
} state_def_t;

state_def_t get_state(int id) {
    state_def_t result;
    if (id > 0) {
        result.status = 1;
        result.value = 100;
    } else {
        result.status = 0;
        result.value = 0;
    }
    return result;
}
```

**期待される出力** (v2.8.0):
```c
void test_01_id_gt_0_T(void) {
    state_def_t result = {0};
    int id = 1;
    
    result = get_state(id);
    
    // 結果を確認
    // TODO: 期待値を設定してください
    TEST_ASSERT_EQUAL(0, result.status);
    TEST_ASSERT_EQUAL(0, result.value);
}
```

### テストケース2: ネストした構造体

**入力**:
```c
typedef struct {
    uint8_t x;
    uint8_t y;
} point_t;

typedef struct {
    point_t position;
    uint8_t color;
} pixel_t;

pixel_t get_pixel(int index) {
    pixel_t result;
    if (index > 0) {
        result.position.x = 10;
        result.position.y = 20;
        result.color = 255;
    }
    return result;
}
```

**期待される出力** (v2.8.0):
```c
void test_01_index_gt_0_T(void) {
    pixel_t result = {0};
    int index = 1;
    
    result = get_pixel(index);
    
    // 結果を確認
    // TODO: 期待値を設定してください
    TEST_ASSERT_EQUAL(0, result.position.x);
    TEST_ASSERT_EQUAL(0, result.position.y);
    TEST_ASSERT_EQUAL(0, result.color);
}
```

### テストケース3: ビットフィールド

**入力**:
```c
typedef struct {
    uint8_t flag1 : 1;
    uint8_t flag2 : 1;
    uint8_t value : 6;
} bit_flags_t;

bit_flags_t get_flags(int mode) {
    bit_flags_t result = {0};
    if (mode > 0) {
        result.flag1 = 1;
        result.value = 10;
    }
    return result;
}
```

**期待される出力** (v2.8.0):
```c
void test_01_mode_gt_0_T(void) {
    bit_flags_t result = {0};
    int mode = 1;
    
    result = get_flags(mode);
    
    // 結果を確認
    // TODO: 期待値を設定してください
    TEST_ASSERT_EQUAL(0, result.flag1);
    TEST_ASSERT_EQUAL(0, result.flag2);
    TEST_ASSERT_EQUAL(0, result.value);
}
```

---

## 🗂️ ファイル構成（v2.7.1）

```
AutoUniTestGen_v2_7_1/
├── VERSION                                  # 2.7.1
├── main.py                                  # エントリーポイント
├── config.ini                               # 設定ファイル
├── standard_types.h                         # 標準型定義
├── standard_macros.h                        # 標準マクロ定義
├── model_presets.json                       # モデルプリセット
├── RELEASE_NOTES_v2_7_1.md                  # リリースノート（新規）
├── doc/
│   ├── design_class_diagram.md              # クラス図（v2.7更新）
│   └── design_sequence_diagram.md           # シーケンス図（v2.7更新）
└── src/
    ├── __init__.py
    ├── cli.py
    ├── c_test_auto_generator.py
    ├── config.py
    ├── data_structures.py                   # ✅ UTF-8対応
    ├── error_handler.py
    ├── performance.py
    ├── template_engine.py
    ├── batch_processor.py
    ├── model_preset_manager.py
    ├── utils.py
    ├── parser/
    │   ├── __init__.py
    │   ├── c_code_parser.py
    │   ├── preprocessor.py
    │   ├── ast_builder.py
    │   ├── condition_extractor.py
    │   ├── typedef_extractor.py
    │   ├── variable_decl_extractor.py
    │   ├── dependency_resolver.py
    │   └── source_definition_extractor.py
    ├── test_generator/
    │   ├── __init__.py
    │   ├── unity_test_generator.py
    │   ├── test_function_generator.py       # ✅ 構造体判定実装
    │   ├── mock_generator.py
    │   ├── prototype_generator.py
    │   ├── comment_generator.py
    │   ├── boundary_value_calculator.py
    │   ├── return_pattern_analyzer.py
    │   └── expectation_inference_engine.py
    ├── truth_table/
    │   ├── __init__.py
    │   ├── truth_table_generator.py
    │   ├── condition_analyzer_v26.py
    │   └── mcdc_pattern_generator_v261.py
    ├── io_table/
    │   ├── __init__.py
    │   ├── io_table_generator.py
    │   └── variable_extractor.py
    ├── output/
    │   ├── __init__.py
    │   └── excel_writer.py
    └── code_extractor/
        ├── __init__.py
        ├── code_extractor.py
        ├── function_extractor.py
        ├── macro_extractor.py
        ├── typedef_extractor.py
        └── variable_extractor.py
```

---

## 💡 重要な注意事項

### UTF-8エンコーディングへの変更

v2.7.1から、生成されるテストコードファイルのエンコーディングがShift_JISからUTF-8に変更されました。

**影響を受ける可能性があるケース**:
1. Shift_JISを前提としたビルドシステム
2. 古いWindowsのメモ帳などのエディタ
3. Shift_JIS指定のMakefile

**対処方法**:
- エディタやIDEをUTF-8に対応させる
- ビルドシステムでUTF-8を指定
- 必要に応じてファイルを変換

### 構造体判定の精度

現在の構造体判定は命名規則に基づく推測的な方法です。

**正しく判定される例**:
- `state_def_t` (typedefのt記法)
- `StateData` (Pascal Case)
- `struct State` (struct キーワード)

**誤判定の可能性がある例**:
- `mystate` (全て小文字)
- `state_data` (スネークケース、_t なし)

---

## 🔗 関連ドキュメント

- `RELEASE_NOTES_v2_7_1.md` - 詳細なリリースノート
- `doc/design_class_diagram.md` - 最新のクラス図
- `doc/design_sequence_diagram.md` - 最新のシーケンス図

---

## 📞 問い合わせ

質問や問題がある場合は、プロジェクトの開発チームに連絡してください。

---

**作成日**: 2025-11-20  
**作成者**: AutoUniTestGen Development Team  
**現在のバージョン**: 2.7.1  
**次のバージョン**: 2.8.0（予定）  
**状態**: ✅ 完成 - 構造体アサーション問題を修正済み
