# AutoUniTestGen v4.2.0 シーケンス図

## 概要
C言語単体テスト自動生成ツールの処理フローを示します。

---

## 1. 全体処理フロー

```mermaid
sequenceDiagram
    autonumber
    participant User
    participant CLI
    participant Generator as CTestAutoGenerator
    participant Parser as CCodeParser
    participant TruthGen as TruthTableGenerator
    participant TestGen as UnityTestGenerator
    participant IOGen as IOTableGenerator
    participant Excel as ExcelWriter
    
    User->>CLI: python main.py -i source.c -f func_name -o output/
    CLI->>CLI: parse_args()
    CLI->>Generator: create(config)
    CLI->>Generator: generate_all(c_file_path, target_function, output_dir)
    
    Note over Generator: Phase 1: ソースコード解析
    Generator->>Parser: parse(source_code, function_name)
    Parser-->>Generator: ParsedData
    
    Note over Generator: Phase 2: 真偽表生成
    Generator->>TruthGen: generate(parsed_data)
    TruthGen-->>Generator: TruthTableData
    Generator->>Excel: write_truth_table(truth_table, path)
    
    Note over Generator: Phase 3: テストコード生成
    Generator->>TestGen: generate(truth_table, parsed_data, source_code)
    TestGen-->>Generator: TestCode
    Generator->>Generator: save_test_code(test_code, path)
    
    Note over Generator: Phase 4: I/O表生成
    Generator->>IOGen: generate(truth_table, parsed_data)
    IOGen-->>Generator: IOTableData
    Generator->>Excel: write_io_table(io_table, path)
    
    Generator-->>CLI: GenerationResult
    CLI-->>User: 完了メッセージ + 出力ファイル一覧
```

---

## 2. ソースコード解析詳細 (CCodeParser.parse)

```mermaid
sequenceDiagram
    autonumber
    participant Gen as CTestAutoGenerator
    participant Parser as CCodeParser
    participant Prep as Preprocessor
    participant Cond as ConditionExtractor
    participant Type as TypedefExtractor
    participant Var as VariableDeclExtractor
    participant Src as SourceDefinitionExtractor
    participant Stdlib as StdlibFunctionExtractor
    participant Dep as DependencyResolver
    
    Gen->>Parser: parse(source_code, function_name)
    
    Note over Parser: Step 1: プリプロセス
    Parser->>Prep: preprocess(source_code)
    Prep->>Prep: expand_macros()
    Prep->>Prep: remove_comments()
    Prep->>Prep: collect_function_macros()
    Prep-->>Parser: preprocessed_code
    
    Note over Parser: Step 2: 型定義抽出
    Parser->>Type: extract_typedefs(code)
    Type-->>Parser: List[TypedefInfo]
    Parser->>Type: extract_struct_definitions()
    Type-->>Parser: List[StructDefinition]
    
    Note over Parser: Step 3: 変数抽出
    Parser->>Var: extract_variables(code)
    Var-->>Parser: List[VariableDeclInfo]
    Parser->>Var: extract_global_variables()
    Var-->>Parser: List[str]
    
    Note over Parser: Step 4: ソース定義抽出
    Parser->>Src: extract_definitions(code)
    Src->>Src: extract_enums()
    Src->>Src: extract_bitfields()
    Src-->>Parser: Dict[definitions]
    
    Note over Parser: Step 5: 条件分岐抽出
    Parser->>Cond: extract_conditions(code, function_name)
    Cond->>Cond: find_if_statements()
    Cond->>Cond: parse_compound_conditions()
    Cond-->>Parser: List[Condition]
    
    Note over Parser: Step 6: 外部関数抽出 (v4.1.1修正)
    Parser->>Parser: _extract_external_functions()
    Parser->>Prep: get_function_macro_names()
    Prep-->>Parser: Set[macro_names]
    Parser->>Stdlib: filter_stdlib_functions(functions)
    Stdlib-->>Parser: List[external_functions]
    Parser->>Parser: functions = functions - macro_names
    
    Note over Parser: Step 7: 関数シグネチャ抽出 (v4.0)
    Parser->>Parser: _extract_function_signatures()
    Parser-->>Parser: Dict[FunctionSignature]
    
    Note over Parser: Step 8: ローカル変数抽出 (v4.2.0 新規)
    Parser->>Parser: _extract_local_variables(code, function_name)
    Parser-->>Parser: Dict[LocalVariableInfo]
    
    Note over Parser: Step 9: 依存関係解決
    Parser->>Dep: resolve_order(typedefs)
    Dep->>Dep: build_dependency_graph()
    Dep->>Dep: topological_sort()
    Dep-->>Parser: sorted_typedefs
    
    Parser->>Parser: create ParsedData (with local_variables)
    Parser-->>Gen: ParsedData
```

---

## 3. ローカル変数抽出詳細 (v4.2.0 新規)

```mermaid
sequenceDiagram
    autonumber
    participant Parser as CCodeParser
    participant Regex as RegexEngine
    
    Note over Parser: _extract_local_variables(code, function_name)
    
    Parser->>Parser: 関数本体を正規表現で抽出
    Note over Parser: static void Utf1(uint8_t Utv1) { ... }
    
    Parser->>Parser: 対応する閉じ括弧を探索
    Parser->>Parser: function_body を取得
    
    loop 各行について
        Parser->>Parser: コメント除去
        Parser->>Parser: for文の初期化部分を除外
        Parser->>Parser: 関数呼び出しを除外
        
        Parser->>Regex: 型名+変数名パターンを検索
        Note over Regex: pattern = r'(\w+)\s+(\w+)\s*(?:=\s*([^;]+))?\s*;'
        
        alt マッチあり
            Regex-->>Parser: type_name, var_name, init_value
            Parser->>Parser: キーワードチェック (if, for, etc.)
            Parser->>Parser: LocalVariableInfo作成
            Note over Parser: {name: Utx73, type: Utx10, scope: Utf1}
        end
    end
    
    Parser-->>Parser: Dict[var_name, LocalVariableInfo]
```

---

## 4. テスト関数生成詳細 (v4.2.0 修正)

```mermaid
sequenceDiagram
    autonumber
    participant Unity as UnityTestGenerator
    participant TFunc as TestFunctionGenerator
    participant Boundary as BoundaryValueCalculator
    participant VResolver as ValueResolver
    participant Comment as CommentGenerator
    
    Unity->>TFunc: generate_test_function(test_case, parsed_data)
    
    TFunc->>Comment: generate_comment(test_case, parsed_data)
    Comment-->>TFunc: comment
    
    TFunc->>TFunc: _generate_test_name()
    
    Note over TFunc: 変数初期化コード生成
    TFunc->>TFunc: _generate_variable_init(test_case, parsed_data)
    
    loop 各条件変数
        TFunc->>Boundary: generate_test_value_with_parsed_data(expr, truth, data)
        
        Note over Boundary: v4.2.0: 数値リテラルチェック
        alt 変数名が数値 (例: "10")
            Boundary-->>TFunc: "// TODO: 数値リテラル 10 は初期化できません"
        else 識別子同士の比較 (>=, <=, >, <)
            Boundary->>VResolver: resolve_smaller_value(value) or resolve_larger_value(value)
            VResolver-->>Boundary: (値, コメント)
            Boundary-->>TFunc: "Utx75.Utm1.Utm11 = 0;  // Utx220より小さい値"
        else 通常の比較
            Boundary-->>TFunc: "variable = value"
        end
        
        Note over TFunc: v4.2.0: 初期化コード後処理
        TFunc->>TFunc: _process_init_code(init, parsed_data, lines)
    end
    
    TFunc->>TFunc: _generate_mock_setup()
    TFunc->>TFunc: _build_function_call_params(parsed_data) v4.1.3
    TFunc->>TFunc: _generate_assertions()
    TFunc->>TFunc: _generate_call_count_check()
    
    TFunc-->>Unity: test_function_code
```

---

## 5. 初期化コード後処理詳細 (v4.2.0 新規)

```mermaid
sequenceDiagram
    autonumber
    participant TFunc as TestFunctionGenerator
    participant PData as ParsedData
    
    Note over TFunc: _process_init_code(init, parsed_data, lines)
    
    alt initがNullまたはコメント
        TFunc-->>TFunc: return init (そのまま)
    end
    
    TFunc->>TFunc: "変数 = 値" 形式からvar_partを抽出
    Note over TFunc: init = "Utx73.Utm13 = 0xDEAD"
    Note over TFunc: var_part = "Utx73.Utm13"
    
    Note over TFunc: 問題3チェック: 数値リテラル
    alt var_partが数値 (例: "10")
        TFunc-->>TFunc: "// TODO: 数値リテラル 10 は変数ではないため初期化できません"
    end
    
    Note over TFunc: 問題2チェック: 構造体メンバー
    alt var_partに "." を含む
        TFunc->>TFunc: root_var = var_part.split('.')[0]
        Note over TFunc: root_var = "Utx73"
        
        Note over TFunc: 問題1チェック: ローカル変数
        TFunc->>TFunc: _is_local_variable(root_var, parsed_data)
        TFunc->>PData: local_variables[root_var]
        
        alt ローカル変数である
            PData-->>TFunc: LocalVariableInfo{type=Utx10}
            TFunc->>TFunc: lines.append("Utx10 Utx73 = {0};  // ローカル変数")
            TFunc-->>TFunc: return init (完全パス維持)
        else グローバル変数
            TFunc-->>TFunc: return init (そのまま)
        end
    end
    
    Note over TFunc: 単独変数のローカル変数チェック
    TFunc->>TFunc: _is_local_variable(var_part, parsed_data)
    alt ローカル変数である
        TFunc->>TFunc: 宣言を追加
        TFunc-->>TFunc: return init
    else グローバル変数
        TFunc-->>TFunc: return init
    end
```

---

## 6. 境界値計算詳細 (v4.2.0 修正)

```mermaid
sequenceDiagram
    autonumber
    participant Boundary as BoundaryValueCalculator
    participant VResolver as ValueResolver
    
    Note over Boundary: generate_test_value_with_parsed_data(expr, truth, data)
    
    Boundary->>Boundary: parse_comparison(expr)
    Note over Boundary: expr = "(Utx75.Utm1.Utm11 >= Utx220)"
    
    Note over Boundary: v4.2.0: 識別子パターン拡張
    Note over Boundary: 新規追加: >=, <=, >, < パターン
    
    Boundary-->>Boundary: {variable: "Utx75.Utm1.Utm11", operator: ">=", value: "Utx220", is_identifier: True}
    
    Note over Boundary: v4.2.0: 数値リテラルチェック
    alt variable.isdigit()
        Boundary-->>Boundary: "// TODO: 数値リテラル X は変数ではないため初期化できません"
    end
    
    alt is_identifier && operator == ">="
        alt truth == "T"
            Boundary-->>Boundary: "variable = value"
            Note over Boundary: Utx75.Utm1.Utm11 = Utx220
        else truth == "F"
            Boundary->>VResolver: resolve_smaller_value("Utx220")
            VResolver-->>Boundary: ("0", "Utx220より小さい値")
            Boundary-->>Boundary: "variable = 0;  // Utx220より小さい値"
        end
    else is_identifier && operator == ">"
        alt truth == "T"
            Boundary->>VResolver: resolve_larger_value("value")
            VResolver-->>Boundary: (larger_value, comment)
        else truth == "F"
            Boundary-->>Boundary: "variable = value"
        end
    end
```

---

## 7. ValueResolver 大小比較処理 (v4.2.0 新規)

```mermaid
sequenceDiagram
    autonumber
    participant VResolver as ValueResolver
    
    Note over VResolver: resolve_smaller_value(value)
    
    alt value が数値
        VResolver->>VResolver: num = parse_numeric(value)
        VResolver->>VResolver: smaller = num - 1
        VResolver-->>VResolver: (str(smaller), "valueより小さい値")
    else value がマクロ定数
        VResolver->>VResolver: macro_val = get_macro_value(value)
        VResolver->>VResolver: num = parse_numeric(macro_val)
        VResolver->>VResolver: smaller = num - 1
        VResolver-->>VResolver: (str(smaller), "value(=macro_val)より小さい値")
    else 不明な識別子
        VResolver-->>VResolver: ("0", "valueより小さい値（境界値）")
    end
    
    Note over VResolver: resolve_larger_value(value)
    
    alt value が数値
        VResolver->>VResolver: num = parse_numeric(value)
        VResolver->>VResolver: larger = num + 1
        VResolver-->>VResolver: (str(larger), "valueより大きい値")
    else value がマクロ定数
        VResolver->>VResolver: macro_val = get_macro_value(value)
        VResolver->>VResolver: num = parse_numeric(macro_val)
        VResolver->>VResolver: larger = num + 1
        VResolver-->>VResolver: (str(larger), "value(=macro_val)より大きい値")
    else 不明な識別子
        VResolver-->>VResolver: ("0xDEAD", "valueより大きい値（境界値）")
    end
```

---

## 8. 真偽表生成詳細 (TruthTableGenerator.generate)

```mermaid
sequenceDiagram
    autonumber
    participant Gen as CTestAutoGenerator
    participant TTGen as TruthTableGenerator
    participant Analyzer as ConditionAnalyzer
    participant MCDC as MCDCPatternGenerator
    
    Gen->>TTGen: generate(parsed_data)
    
    loop 各条件について
        TTGen->>Analyzer: analyze(condition)
        
        alt 単純条件 (SIMPLE_IF)
            Analyzer->>Analyzer: _analyze_simple_condition()
            Analyzer-->>TTGen: AnalyzedCondition
            TTGen->>MCDC: generate_patterns(condition)
            Note over MCDC: T, F の2パターン
            MCDC-->>TTGen: [T, F]
            
        else OR条件 (A || B || C)
            Analyzer->>Analyzer: _analyze_compound_condition()
            Analyzer->>Analyzer: split_conditions('||')
            Analyzer-->>TTGen: AnalyzedCondition(conditions=[A,B,C])
            TTGen->>MCDC: generate_or_patterns(3)
            Note over MCDC: TXX, FTX, FFT, FFF の4パターン
            MCDC-->>TTGen: [TXX, FTX, FFT, FFF]
            
        else AND条件 (A && B && C)
            Analyzer->>Analyzer: _analyze_compound_condition()
            Analyzer->>Analyzer: split_conditions('&&')
            Analyzer-->>TTGen: AnalyzedCondition(conditions=[A,B,C])
            TTGen->>MCDC: generate_and_patterns(3)
            Note over MCDC: TTT, FXX, TFX, TTF の4パターン
            MCDC-->>TTGen: [TTT, FXX, TFX, TTF]
            
        else ネスト条件 (A || (B && C))
            Analyzer->>Analyzer: _analyze_nested_condition()
            Analyzer-->>TTGen: AnalyzedCondition(nested)
            TTGen->>MCDC: generate_nested_patterns(condition)
            Note over MCDC: 再帰的にパターン生成
            MCDC-->>TTGen: patterns
        end
        
        TTGen->>TTGen: create TestCase for each pattern
    end
    
    TTGen->>TTGen: create TruthTableData
    TTGen-->>Gen: TruthTableData
```

---

## 9. モックリセット関数生成詳細 (v4.1.2)

```mermaid
sequenceDiagram
    autonumber
    participant Mock as MockGenerator
    
    Note over Mock: generate_reset_function()
    Mock->>Mock: lines = ["static void reset_all_mocks(void) {"]
    
    loop 各関数のモック変数
        Mock->>Mock: get return_value type
        Mock->>Mock: _is_primitive_type(type)?
        
        alt プリミティブ型 (int, uint8_t, bool, etc.)
            Mock->>Mock: "mock_XXX_return_value = 0;"
        else ポインタ型 (* in type)
            Mock->>Mock: "mock_XXX_return_value = NULL;"
        else 構造体/union型
            Mock->>Mock: "memset(&mock_XXX_return_value, 0, sizeof(...));"
            Mock->>Mock: _needs_string_h = True
        end
        
        Mock->>Mock: "mock_XXX_call_count = 0;"
        
        loop 各パラメータ
            Mock->>Mock: get param type
            Mock->>Mock: _get_init_code(param_name, param_type)
        end
    end
    
    Mock->>Mock: lines.append("}")
    Mock-->>Mock: reset_function_code
```

---

## 10. I/O表生成詳細

```mermaid
sequenceDiagram
    autonumber
    participant Gen as CTestAutoGenerator
    participant IOGen as IOTableGenerator
    participant VarExt as IOVariableExtractor
    
    Gen->>IOGen: generate(truth_table, parsed_data)
    
    IOGen->>IOGen: collect_input_variables(parsed_data)
    Note over IOGen: グローバル変数 + 関数パラメータ
    
    IOGen->>IOGen: collect_output_variables(parsed_data)
    Note over IOGen: グローバル変数 + 戻り値
    
    loop 各テストケース
        IOGen->>VarExt: extract_io_variables(test_case, parsed_data)
        VarExt->>VarExt: extract_inputs_from_condition()
        VarExt->>VarExt: extract_outputs_from_expected()
        VarExt-->>IOGen: {inputs: {...}, outputs: {...}}
        IOGen->>IOGen: add_test_data(io_data)
    end
    
    IOGen->>IOGen: create IOTableData
    IOGen-->>Gen: IOTableData
```

---

## v4.2.0 修正フロー全体図

```mermaid
flowchart TB
    subgraph Input["入力"]
        A[C言語ソースコード]
    end
    
    subgraph Parse["解析フェーズ v4.2.0"]
        B[CCodeParser.parse]
        C[_extract_local_variables]
        D[LocalVariableInfo辞書]
    end
    
    subgraph Generate["テストコード生成フェーズ v4.2.0"]
        E[TestFunctionGenerator]
        F[_generate_variable_init]
        G[BoundaryValueCalculator.generate_test_value_with_parsed_data]
        H{数値リテラル?}
        I{構造体メンバー?}
        J{ローカル変数?}
        K[_process_init_code]
        L[ValueResolver.resolve_smaller/larger_value]
    end
    
    subgraph Output["出力"]
        M[テストコード]
    end
    
    A --> B
    B --> C
    C --> D
    D --> E
    E --> F
    F --> G
    G --> H
    H -->|Yes| N["// TODO: 数値リテラル..."]
    H -->|No| I
    I -->|Yes 完全パス維持| K
    I -->|No| J
    J -->|Yes| O[ローカル変数宣言追加]
    J -->|No| P[グローバル変数初期化]
    K --> J
    G --> L
    L --> K
    N --> M
    O --> M
    P --> M
```

---

## エラーハンドリングフロー

```mermaid
sequenceDiagram
    autonumber
    participant User
    participant CLI
    participant Gen as CTestAutoGenerator
    participant Parser as CCodeParser
    
    User->>CLI: main.py -i invalid.c -f func
    CLI->>Gen: generate_all()
    
    alt ファイルが存在しない
        Gen-->>CLI: GenerationResult(success=False, error="ファイルが見つかりません")
    else パース失敗
        Gen->>Parser: parse()
        Parser-->>Gen: ParseError
        Gen-->>CLI: GenerationResult(success=False, error="パースエラー")
    else 関数が見つからない
        Gen->>Parser: parse()
        Parser-->>Gen: ParsedData(conditions=[])
        Gen-->>CLI: GenerationResult(success=False, error="関数が見つかりません")
    else 成功
        Gen-->>CLI: GenerationResult(success=True, paths=[...])
    end
    
    CLI->>User: エラーメッセージまたは成功メッセージ
```

---

**バージョン**: v4.2.0
**作成日**: 2025-12-02
