# C言語単体テスト自動生成ツール - クラス図 v2.6.0

**更新日**: 2025-11-19  
**バージョン**: v2.6.0  
**主な変更**: MCDCPatternGeneratorとConditionAnalyzerの拡張

---

## 全体構成図

```mermaid
classDiagram
    class CTestAutoGenerator {
        -CCodeParser parser
        -TruthTableGenerator truth_table_gen
        -UnityTestGenerator test_generator
        -IOTableGenerator io_table_gen
        -ExcelWriter excel_writer
        +__init__()
        +generate_all(c_file_path, output_dir) dict
        +_validate_input(c_file_path) bool
    }

    class CCodeParser {
        -Preprocessor preprocessor
        -ASTBuilder ast_builder
        -ConditionExtractor cond_extractor
        -TypedefExtractor typedef_extractor
        -VariableDeclExtractor var_extractor
        +parse(c_file_path, target_function) ParsedData
        -_read_file(path) str
        -_extract_function_info(ast) dict
        -_extract_typedefs(ast) list
        -_extract_variables(ast) list
    }

    class Preprocessor {
        -dict defines
        -list include_paths
        -Logger logger
        +preprocess(code) str
        -_remove_comments(code) str
        -_process_defines(code) str
        -_handle_includes(code) str
        -_expand_macros(code) str
    }

    class ASTBuilder {
        -pycparser.CParser parser
        -Logger logger
        +build_ast(code) AST
        -_add_fake_includes(code) str
        -_handle_parse_error(error) None
    }

    class ConditionExtractor {
        -list conditions
        -int current_line
        -str current_function
        -Logger logger
        +extract_conditions(ast) list
        +visit_FuncDef(node) None
        +visit_If(node) None
        +visit_Switch(node) None
        -_analyze_binary_op(node) dict
        -_extract_all_conditions(node, operator) list
        -_extract_switch_cases(node) list
        -_node_to_str(node) str
    }

    class TruthTableGenerator {
        -ConditionAnalyzer analyzer
        -MCDCPatternGenerator mcdc_gen
        -Logger logger
        +generate(parsed_data) TruthTableData
        -_generate_test_number() int
        -_format_table_row(condition, pattern) dict
    }

    class ConditionAnalyzer {
        <<v2.6.0 Enhanced>>
        -Logger logger
        +analyze_condition(condition) dict
        -_analyze_simple_condition(condition) dict
        -_analyze_or_condition(condition) dict
        -_analyze_and_condition(condition) dict
        -_analyze_switch(condition) dict
        -_suggest_test_values(expression) dict
        -_parse_comparison(expression) dict
        +is_simple_condition(expression) bool
        +is_or_condition(expression) bool
        +is_and_condition(expression) bool
        +split_binary_condition(expression, operator) tuple
        -_remove_outer_parentheses(expr) str
    }

    class MCDCPatternGenerator {
        <<v2.6.0 Major Update>>
        -Logger logger
        +generate_or_patterns(n_conditions) list
        +generate_and_patterns(n_conditions) list
        +generate_switch_patterns(cases) list
        +generate_mcdc_patterns_for_complex(top_operator, conditions) list
        -_extract_or_conditions(condition) list
        -_extract_and_conditions(condition) list
        -_extract_mixed_conditions(condition) list
        -_remove_outer_parens(expr) str
        -_generate_patterns_for_structure(top_operator, conditions, structure) list
        -_generate_or_group_patterns_with_structure(top_operator, total, start, count, structure) set
        -_generate_and_group_patterns(top_operator, total, start, count) set
        -_generate_simple_condition_patterns_with_structure(top_operator, total, index, structure) set
        -_create_base_pattern_for_and(total, structure) list
        +pattern_to_string(pattern) str
        +explain_pattern(pattern, operator) str
    }

    class UnityTestGenerator {
        -MockGenerator mock_gen
        -TestFunctionGenerator func_gen
        -CommentGenerator comment_gen
        -PrototypeGenerator proto_gen
        -Logger logger
        +generate(truth_table, parsed_data) TestCode
        -_generate_header() str
        -_generate_includes() str
        -_generate_setup_teardown() str
        -_combine_all_parts() str
    }

    class MockGenerator {
        -list external_functions
        -dict mock_templates
        -Logger logger
        +generate_mocks(parsed_data) str
        +generate_mock_variables() str
        +generate_mock_functions() str
        +generate_reset_function() str
        -_get_return_type(func_name) str
        -_generate_call_counter() str
    }

    class TestFunctionGenerator {
        -BoundaryValueCalculator boundary_calc
        -Logger logger
        +generate_test_function(test_case, parsed_data) str
        -_generate_test_name(test_case) str
        -_generate_variable_init(test_case) str
        -_generate_mock_setup(test_case) str
        -_generate_function_call(test_case) str
        -_generate_assertions(test_case) str
    }

    class BoundaryValueCalculator {
        -Logger logger
        +calculate_boundary_values(condition, truth_value) dict
        -_parse_comparison_operator(condition) dict
        -_calculate_for_greater_than(value, is_true) int
        -_calculate_for_less_than(value, is_true) int
        -_calculate_for_equal(value, is_true) int
    }

    class CommentGenerator {
        -Logger logger
        +generate_comment(test_case, parsed_data) str
        -_format_condition_description(condition) str
        -_format_truth_pattern(pattern) str
        -_format_expected_behavior(expected) str
    }

    class PrototypeGenerator {
        -Logger logger
        +generate_prototypes(functions, mocks) str
        -_generate_static_declaration(func_name) str
        -_sort_declarations(declarations) list
    }

    class IOTableGenerator {
        -VariableExtractor var_extractor
        -Logger logger
        +generate(test_code, truth_table) IOTableData
        -_extract_io_mapping(test_code, test_case) dict
        -_format_io_table_row(test_case, io_data) dict
    }

    class VariableExtractor {
        -Logger logger
        +extract_input_variables(test_code) list
        +extract_output_variables(test_code) list
        -_parse_assignment_statements(code) list
        -_parse_assert_statements(code) list
    }

    class ExcelWriter {
        -Logger logger
        +write_truth_table(truth_table_data, output_path) None
        +write_io_table(io_table_data, output_path) None
        -_create_workbook() Workbook
        -_format_header(worksheet) None
        -_write_data_rows(worksheet, data) None
        -_apply_borders(worksheet) None
    }

    %% 関係性
    CTestAutoGenerator --> CCodeParser
    CTestAutoGenerator --> TruthTableGenerator
    CTestAutoGenerator --> UnityTestGenerator
    CTestAutoGenerator --> IOTableGenerator
    CTestAutoGenerator --> ExcelWriter

    CCodeParser --> Preprocessor
    CCodeParser --> ASTBuilder
    CCodeParser --> ConditionExtractor

    TruthTableGenerator --> ConditionAnalyzer
    TruthTableGenerator --> MCDCPatternGenerator

    ConditionAnalyzer --> MCDCPatternGenerator : v2.6.0 uses

    UnityTestGenerator --> MockGenerator
    UnityTestGenerator --> TestFunctionGenerator
    UnityTestGenerator --> CommentGenerator
    UnityTestGenerator --> PrototypeGenerator

    TestFunctionGenerator --> BoundaryValueCalculator

    IOTableGenerator --> VariableExtractor
```

---

## MCDCPatternGenerator詳細（v2.6.0拡張）

```mermaid
classDiagram
    class MCDCPatternGenerator {
        <<v2.6.0 Major Update>>
        -Logger logger
        
        %% 既存メソッド（後方互換性）
        +generate_or_patterns(n_conditions: int) List~str~
        +generate_and_patterns(n_conditions: int) List~str~
        +generate_switch_patterns(cases: List) List~str~
        +pattern_to_string(pattern: Tuple) str
        +explain_pattern(pattern: str, operator: str) str
        
        %% v2.6.0 新規メソッド
        +generate_mcdc_patterns_for_complex(top_operator: str, conditions: List~str~) List~str~
        
        %% v2.6.0 条件展開メソッド
        -_extract_or_conditions(condition: str) List~str~
        -_extract_and_conditions(condition: str) List~str~
        -_extract_mixed_conditions(condition: str) List~str~
        -_remove_outer_parens(expr: str) str
        
        %% v2.6.0 パターン生成メソッド
        -_generate_patterns_for_structure(top_operator: str, conditions: List~str~, structure: List~Tuple~) List~str~
        -_generate_or_group_patterns_with_structure(top_operator: str, total: int, start_index: int, count: int, structure: List~Tuple~) Set~Tuple~
        -_generate_and_group_patterns(top_operator: str, total: int, start_index: int, count: int) Set~Tuple~
        -_generate_simple_condition_patterns_with_structure(top_operator: str, total: int, index: int, structure: List~Tuple~) Set~Tuple~
        
        %% v2.6.0 補助メソッド
        -_create_base_pattern_for_and(total: int, structure: List~Tuple~) List~bool~
    }

    class ConditionStructure {
        <<Data Structure>>
        +operator: str
        +count: int
    }

    class PatternSet {
        <<Set of Tuples>>
        +patterns: Set~Tuple~bool~~
    }

    MCDCPatternGenerator ..> ConditionStructure : uses
    MCDCPatternGenerator ..> PatternSet : generates
```

---

## ConditionAnalyzer詳細（v2.6.0拡張）

```mermaid
classDiagram
    class ConditionAnalyzer {
        <<v2.6.0 Enhanced>>
        -Logger logger
        
        %% 公開メソッド
        +analyze_condition(condition: Condition) Dict
        +is_simple_condition(expression: str) bool
        +is_or_condition(expression: str) bool
        +is_and_condition(expression: str) bool
        +split_binary_condition(expression: str, operator: str) Tuple
        
        %% 内部分析メソッド
        -_analyze_simple_condition(condition: Condition) Dict
        -_analyze_or_condition(condition: Condition) Dict
        -_analyze_and_condition(condition: Condition) Dict
        -_analyze_switch(condition: Condition) Dict
        
        %% v2.6.0 ネスト検出
        -_detect_nested_structure(conditions: List~str~) bool
        
        %% テスト値提案
        -_suggest_test_values(expression: str) Dict
        -_parse_comparison(expression: str) Optional~Dict~
        
        %% ユーティリティ
        -_remove_outer_parentheses(expr: str) str
    }

    class Condition {
        <<Data Class>>
        +line: int
        +type: ConditionType
        +expression: str
        +operator: Optional~str~
        +left: Optional~str~
        +right: Optional~str~
        +conditions: Optional~List~str~~
        +cases: Optional~List~
        +ast_node: Optional
        +parent_context: str
    }

    class ConditionType {
        <<Enum>>
        SIMPLE_IF
        OR_CONDITION
        AND_CONDITION
        SWITCH
    }

    class AnalysisResult {
        <<Dict>>
        +type: str
        +expression: str
        +patterns: List~str~
        +description: str
        +has_nested: bool
        +mcdc_explanation: Dict
    }

    ConditionAnalyzer ..> Condition : analyzes
    ConditionAnalyzer ..> ConditionType : uses
    ConditionAnalyzer ..> AnalysisResult : returns
    Condition --> ConditionType : has
```

---

## データ構造クラス

```mermaid
classDiagram
    class ParsedData {
        +file_name: str
        +function_name: str
        +conditions: List~Condition~
        +external_functions: List~str~
        +global_variables: List~str~
        +typedefs: List~TypeDef~
        +variable_declarations: List~VarDecl~
        +macro_definitions: List~MacroDef~
    }

    class Condition {
        +line: int
        +type: ConditionType
        +expression: str
        +operator: Optional~str~
        +left: Optional~str~
        +right: Optional~str~
        +conditions: Optional~List~str~~
        +cases: Optional~List~
        +ast_node: Optional
        +parent_context: str
    }

    class TruthTableData {
        +test_cases: List~TestCase~
        +total_patterns: int
        +mcdc_coverage: float
    }

    class TestCase {
        +no: int
        +truth: str
        +condition: str
        +expected: str
        +pattern_explanation: Optional~str~
    }

    class TestCode {
        +header: str
        +includes: str
        +typedefs: str
        +mocks: str
        +prototypes: str
        +setup_teardown: str
        +test_functions: List~str~
        +full_code: str
    }

    class IOTableData {
        +test_cases: List~IOTestCase~
        +input_variables: List~str~
        +output_variables: List~str~
    }

    class IOTestCase {
        +no: int
        +input_values: Dict
        +output_values: Dict
    }

    ParsedData --> Condition : contains
    TruthTableData --> TestCase : contains
    IOTableData --> IOTestCase : contains
```

---

## v2.6.0の主要な変更点

### 1. MCDCPatternGenerator

**新機能**:
- `generate_mcdc_patterns_for_complex()`: ネスト条件の処理
- 再帰的なOR/AND展開メソッド
- 構造ベースのパターン生成

**処理フロー**:
```
条件展開 → 構造分析 → パターン生成 → 重複削除
```

### 2. ConditionAnalyzer

**強化内容**:
- ネスト構造の自動検出
- 複雑条件の自動判定
- 新メソッドへの自動切り替え

**判定ロジック**:
```python
has_nested = any('||' in cond or '&&' in cond for cond in conditions)
if has_nested:
    # 新メソッド使用
    patterns = mcdc_gen.generate_mcdc_patterns_for_complex(...)
else:
    # 従来メソッド
    patterns = mcdc_gen.generate_and_patterns(...)
```

---

## クラス間の依存関係

```mermaid
graph TD
    A[CTestAutoGenerator] --> B[CCodeParser]
    A --> C[TruthTableGenerator]
    A --> D[UnityTestGenerator]
    A --> E[IOTableGenerator]
    A --> F[ExcelWriter]
    
    B --> G[Preprocessor]
    B --> H[ASTBuilder]
    B --> I[ConditionExtractor]
    
    C --> J[ConditionAnalyzer]
    C --> K[MCDCPatternGenerator]
    
    J --> K
    
    D --> L[MockGenerator]
    D --> M[TestFunctionGenerator]
    D --> N[CommentGenerator]
    D --> O[PrototypeGenerator]
    
    M --> P[BoundaryValueCalculator]
    
    E --> Q[VariableExtractor]
    
    style K fill:#ff9,stroke:#333,stroke-width:4px
    style J fill:#ff9,stroke:#333,stroke-width:4px
```

**凡例**:
- 🟨 黄色: v2.6.0で大幅拡張されたクラス

---

## メソッド複雑度（v2.6.0）

| クラス | メソッド | 複雑度 | 行数 |
|--------|----------|--------|------|
| MCDCPatternGenerator | generate_mcdc_patterns_for_complex | 高 | ~50 |
| MCDCPatternGenerator | _extract_or_conditions | 中 | ~40 |
| MCDCPatternGenerator | _generate_patterns_for_structure | 高 | ~60 |
| ConditionAnalyzer | _analyze_and_condition | 中 | ~60 |
| ConditionAnalyzer | _analyze_or_condition | 中 | ~60 |

---

## 設計原則

### 1. 単一責任の原則（SRP）
各クラスは1つの責任のみを持つ:
- `MCDCPatternGenerator`: パターン生成のみ
- `ConditionAnalyzer`: 条件分析のみ
- `TruthTableGenerator`: 真偽表生成のみ

### 2. 開放閉鎖の原則（OCP）
- 新しいメソッドを追加（`generate_mcdc_patterns_for_complex`）
- 既存メソッドは変更なし（後方互換性）

### 3. 依存性逆転の原則（DIP）
- `ConditionAnalyzer`は`MCDCPatternGenerator`に依存
- インターフェースを通じた疎結合

---

## 変更履歴

### v2.6.0 (2025-11-19)
- ✅ MCDCPatternGeneratorに7つの新規メソッド追加
- ✅ ConditionAnalyzerのネスト検出機能追加
- ✅ データ構造にhas_nestedフラグ追加
- ✅ 再帰的展開アルゴリズムの実装

### v2.5.0以前
- 基本的なクラス構成
- 単純なOR/AND条件のみ対応

---

**注**: このクラス図は、v2.6.0で実装されたネストしたAND/OR条件のMC/DC処理を正確に反映しています。
