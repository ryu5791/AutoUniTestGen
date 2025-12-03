# C言語単体テスト自動生成ツール - シーケンス図 (v4.3.3.1)

## 1. 全体処理フロー

```mermaid
sequenceDiagram
    actor User
    participant Main as CTestAutoGenerator
    participant Parser as CCodeParser
    participant TruthTable as TruthTableGenerator
    participant TestGen as UnityTestGenerator
    participant IOTable as IOTableGenerator
    participant Excel as ExcelWriter

    User->>Main: C言語ファイル、関数名を指定
    
    Note over Main: Step 1: C言語解析
    Main->>Parser: parse(c_file_path, function_name)
    Parser->>Parser: プリプロセス処理
    Parser->>Parser: AST生成
    Parser->>Parser: 条件分岐抽出
    Parser->>Parser: 型定義・変数宣言抽出
    Parser->>Parser: 関数シグネチャ抽出
    Parser->>Parser: ローカル変数抽出
    Parser-->>Main: ParsedData
    
    Note over Main: Step 2: 真偽表生成
    Main->>TruthTable: generate(parsed_data)
    TruthTable->>TruthTable: 条件解析（OR/AND/switch）
    TruthTable->>TruthTable: MC/DCパターン生成
    TruthTable-->>Main: TruthTableData
    
    Main->>Excel: write_truth_table(table_data, filepath)
    Excel-->>Main: truth_table.xlsx
    
    Note over Main: Step 3: テストコード生成
    Main->>TestGen: generate(truth_table, parsed_data)
    TestGen->>TestGen: 型定義生成
    TestGen->>TestGen: モック/スタブ生成
    TestGen->>TestGen: テスト関数生成
    TestGen->>TestGen: main関数生成
    TestGen-->>Main: TestCode
    
    Main->>TestGen: save(output_path)
    TestGen-->>Main: test_xxx.c
    
    Note over Main: Step 4: I/O表生成
    Main->>IOTable: generate(truth_table, parsed_data)
    IOTable->>IOTable: 入出力変数抽出
    IOTable-->>Main: IOTableData
    
    Main->>Excel: write_io_table(io_table_data, filepath)
    Excel-->>Main: io_table.xlsx
    
    Main-->>User: 完了通知（3ファイル生成）
```

## 2. CCodeParser詳細シーケンス

```mermaid
sequenceDiagram
    participant Main as CTestAutoGenerator
    participant Parser as CCodeParser
    participant Preprocessor as Preprocessor
    participant ASTBuilder as ASTBuilder
    participant CondExtractor as ConditionExtractor
    participant TypedefExt as TypedefExtractor
    participant VarExt as VariableDeclExtractor
    participant SourceDef as SourceDefinitionExtractor

    Main->>Parser: parse(c_file_path, function_name)
    
    Parser->>Preprocessor: preprocess(c_code)
    Note over Preprocessor: プリプロセス処理
    Preprocessor->>Preprocessor: コメント削除
    Preprocessor->>Preprocessor: #define抽出
    Preprocessor->>Preprocessor: 関数マクロ抽出
    Preprocessor->>Preprocessor: ビットフィールド情報抽出
    Preprocessor-->>Parser: preprocessed_code, macros, bitfields
    
    Parser->>ASTBuilder: build_ast(preprocessed_code)
    Note over ASTBuilder: pycparserでAST構築
    ASTBuilder->>ASTBuilder: fake_libc_include使用
    ASTBuilder-->>Parser: ast
    
    Parser->>CondExtractor: extract_conditions(ast, function_name)
    Note over CondExtractor: 条件分岐を抽出
    CondExtractor->>CondExtractor: visit_If()
    CondExtractor->>CondExtractor: visit_Switch()
    CondExtractor->>CondExtractor: OR/AND条件分解
    CondExtractor-->>Parser: conditions_list
    
    Parser->>TypedefExt: extract_typedefs(code)
    TypedefExt-->>Parser: typedefs
    
    Parser->>TypedefExt: extract_struct_definitions(code)
    TypedefExt-->>Parser: struct_definitions
    
    Parser->>VarExt: extract_variables(code)
    VarExt-->>Parser: variables
    
    Parser->>SourceDef: extract_macros(code)
    SourceDef-->>Parser: macro_definitions
    
    Parser->>Parser: _extract_function_signatures(ast)
    Parser->>Parser: _extract_local_variables(code, function_name)
    
    Parser-->>Main: ParsedData
```

## 3. TruthTableGenerator詳細シーケンス

```mermaid
sequenceDiagram
    participant Main as CTestAutoGenerator
    participant TruthGen as TruthTableGenerator
    participant CondAnalyzer as ConditionAnalyzer
    participant MCDCGen as MCDCPatternGenerator

    Main->>TruthGen: generate(parsed_data)
    
    loop 各条件分岐
        TruthGen->>CondAnalyzer: analyze_condition(condition)
        
        alt 単純if文
            CondAnalyzer-->>TruthGen: {type: "simple"}
            TruthGen->>MCDCGen: generate_simple_patterns()
            MCDCGen-->>TruthGen: ["T", "F"]
            
        else OR条件 (A || B || C)
            CondAnalyzer->>CondAnalyzer: 条件を分解
            CondAnalyzer-->>TruthGen: {type: "or", n_conditions: 3}
            TruthGen->>MCDCGen: generate_or_patterns(3)
            MCDCGen-->>TruthGen: ["TFF", "FTF", "FFT", "FFF"]
            
        else AND条件 (A && B && C)
            CondAnalyzer->>CondAnalyzer: 条件を分解
            CondAnalyzer-->>TruthGen: {type: "and", n_conditions: 3}
            TruthGen->>MCDCGen: generate_and_patterns(3)
            MCDCGen-->>TruthGen: ["TFT", "TTF", "TTT", "FTT"]
            
        else switch文
            CondAnalyzer->>CondAnalyzer: case値を抽出
            CondAnalyzer-->>TruthGen: {type: "switch", cases: [...]}
            TruthGen->>MCDCGen: generate_switch_patterns(cases)
            MCDCGen-->>TruthGen: 各case + default
        end
        
        TruthGen->>TruthGen: TestCase作成
    end
    
    TruthGen->>TruthGen: テスト番号採番
    TruthGen-->>Main: TruthTableData
```

## 4. UnityTestGenerator詳細シーケンス

```mermaid
sequenceDiagram
    participant Main as CTestAutoGenerator
    participant TestGen as UnityTestGenerator
    participant DepResolver as DependencyResolver
    participant MockGen as MockGenerator
    participant ProtoGen as PrototypeGenerator
    participant TestFuncGen as TestFunctionGenerator
    participant CommentGen as CommentGenerator

    Main->>TestGen: generate(truth_table, parsed_data)
    
    Note over TestGen: ヘッダー・インクルード生成
    TestGen->>TestGen: _generate_header()
    TestGen->>TestGen: _generate_includes()
    
    Note over TestGen: 型定義生成（依存順序でソート）
    TestGen->>DepResolver: sort_typedefs(parsed_data.typedefs)
    DepResolver-->>TestGen: sorted_typedefs
    TestGen->>TestGen: _generate_type_definitions()
    
    Note over TestGen: モック/スタブ生成
    TestGen->>MockGen: generate_mock_variables(parsed_data)
    MockGen-->>TestGen: mock_variables_code
    
    TestGen->>MockGen: generate_mock_functions(parsed_data)
    MockGen->>MockGen: 関数シグネチャ参照
    MockGen->>MockGen: 戻り値・パラメータ一致
    MockGen-->>TestGen: mock_functions_code
    
    TestGen->>MockGen: generate_reset_function()
    MockGen-->>TestGen: reset_all_mocks_code
    
    Note over TestGen: プロトタイプ宣言生成
    TestGen->>ProtoGen: generate_mock_prototypes(parsed_data)
    ProtoGen-->>TestGen: mock_prototypes
    
    Note over TestGen: テスト関数生成
    loop 各テストケース
        TestGen->>CommentGen: generate_comment(test_case, parsed_data)
        CommentGen-->>TestGen: comment_text
        
        TestGen->>TestFuncGen: generate_test_function(test_case, parsed_data)
        TestFuncGen->>TestFuncGen: テスト名生成
        TestFuncGen->>TestFuncGen: 変数初期化コード生成
        TestFuncGen->>TestFuncGen: 対象関数呼び出し
        TestFuncGen->>TestFuncGen: アサーション生成
        TestFuncGen-->>TestGen: test_function_code
    end
    
    Note over TestGen: main関数生成
    TestGen->>TestGen: _generate_main_function(test_cases)
    
    TestGen-->>Main: TestCode
```

## 5. TestFunctionGenerator詳細シーケンス (v4.3.3.1)

```mermaid
sequenceDiagram
    participant TestGen as UnityTestGenerator
    participant FuncGen as TestFunctionGenerator
    participant Checker as AssignableVariableChecker
    participant BoundaryCalc as BoundaryValueCalculator
    participant ValueRes as ValueResolver
    participant CommentGen as CommentGenerator

    TestGen->>FuncGen: generate_test_function(test_case, parsed_data)
    
    Note over FuncGen: コメント生成
    FuncGen->>CommentGen: generate_comment(test_case, parsed_data)
    CommentGen-->>FuncGen: comment_text
    
    Note over FuncGen: テスト名生成
    FuncGen->>FuncGen: _generate_test_name(test_case, parsed_data)
    
    Note over FuncGen: 変数初期化コード生成
    FuncGen->>FuncGen: _generate_variable_init(test_case, parsed_data)
    
    loop 各条件の初期化
        FuncGen->>BoundaryCalc: generate_test_value_with_parsed_data(expr, truth, parsed_data)
        BoundaryCalc->>ValueRes: resolve_value(identifier)
        ValueRes-->>BoundaryCalc: resolved_value
        BoundaryCalc-->>FuncGen: init_code
        
        Note over FuncGen: v4.3.3.1: 代入可能性チェック
        FuncGen->>FuncGen: _process_init_code(init, parsed_data, lines)
        FuncGen->>Checker: is_assignable(var_name)
        
        alt 代入可能
            Checker-->>FuncGen: True
            FuncGen->>FuncGen: 初期化コードを出力
        else 代入不可
            Checker-->>FuncGen: False
            FuncGen->>Checker: get_reason(var_name)
            Checker-->>FuncGen: "理由メッセージ"
            FuncGen->>FuncGen: TODOコメントを出力
        end
    end
    
    Note over FuncGen: モック設定
    FuncGen->>FuncGen: _generate_mock_setup(test_case, parsed_data)
    
    Note over FuncGen: 対象関数呼び出し
    FuncGen->>FuncGen: _build_function_call_params(parsed_data)
    
    Note over FuncGen: アサーション生成
    FuncGen->>FuncGen: _generate_assertions(test_case, parsed_data)
    
    Note over FuncGen: 呼び出し回数チェック
    FuncGen->>FuncGen: _generate_call_count_check(test_case, parsed_data)
    
    FuncGen-->>TestGen: test_function_code
```

## 6. AssignableVariableChecker詳細シーケンス (v4.3.3.1 新規)

```mermaid
sequenceDiagram
    participant FuncGen as TestFunctionGenerator
    participant Checker as AssignableVariableChecker
    participant ParsedData as ParsedData

    FuncGen->>Checker: __init__(parsed_data)
    
    Note over Checker: 非代入可能セット構築
    Checker->>Checker: _build_non_assignable_set()
    Checker->>ParsedData: local_variables
    Checker->>Checker: ローカル変数を追加
    Checker->>Checker: ループ変数を追加
    Checker->>ParsedData: struct_definitions
    Checker->>Checker: 構造体メンバー名を追加
    Checker->>ParsedData: enum_values
    Checker->>Checker: enum定数を追加
    Checker->>ParsedData: external_functions
    Checker->>Checker: 関数名を追加
    Checker->>ParsedData: macros
    Checker->>Checker: マクロを追加
    
    Note over Checker: 代入可能セット構築
    Checker->>Checker: _build_assignable_set()
    Checker->>ParsedData: global_variables
    Checker->>Checker: グローバル変数を追加
    Checker->>ParsedData: function_info.parameters
    Checker->>Checker: パラメータを追加
    
    FuncGen->>Checker: is_assignable("Utv19")
    Checker->>Checker: _is_root_assignable("Utv19")
    Note over Checker: non_assignable優先でチェック
    alt non_assignableに含まれる
        Checker-->>FuncGen: False
    else assignable_varsに含まれる
        Checker-->>FuncGen: True
    else どちらにもない
        Checker-->>FuncGen: False (未知=ローカル推測)
    end
    
    FuncGen->>Checker: get_reason("Utv19")
    Checker->>Checker: get_reason_code("Utv19")
    Checker->>Checker: _format_reason(name, code)
    Checker-->>FuncGen: "Utv19はfor文のループ変数のため直接初期化できません"
```

## 7. MockGenerator詳細シーケンス

```mermaid
sequenceDiagram
    participant TestGen as UnityTestGenerator
    participant MockGen as MockGenerator
    participant ParsedData as ParsedData

    TestGen->>MockGen: generate_mock_variables(parsed_data)
    
    loop 各外部関数
        MockGen->>ParsedData: function_signatures[func_name]
        
        alt シグネチャあり
            ParsedData-->>MockGen: FunctionSignature
            MockGen->>MockGen: 戻り値型取得
        else シグネチャなし
            MockGen->>MockGen: デフォルト型(int)使用
        end
        
        MockGen->>MockGen: 戻り値変数生成 (mock_xxx_return_value)
        MockGen->>MockGen: 呼び出し回数変数生成 (mock_xxx_call_count)
    end
    MockGen-->>TestGen: mock_variables_code
    
    TestGen->>MockGen: generate_mock_functions(parsed_data)
    
    loop 各外部関数
        MockGen->>ParsedData: function_signatures[func_name]
        MockGen->>MockGen: パラメータリスト取得
        MockGen->>MockGen: モック関数本体生成
        Note over MockGen: call_count++, return mock_xxx_return_value
    end
    MockGen-->>TestGen: mock_functions_code
```

## 8. データフロー概要

```mermaid
flowchart TB
    subgraph Input
        CFile[C言語ソースファイル]
        FuncName[関数名]
    end
    
    subgraph Parser
        CFile --> Preprocessor
        Preprocessor --> ASTBuilder
        ASTBuilder --> ConditionExtractor
        ConditionExtractor --> ParsedData
    end
    
    subgraph TruthTableGen
        ParsedData --> ConditionAnalyzer
        ConditionAnalyzer --> MCDCPatternGenerator
        MCDCPatternGenerator --> TruthTableData
    end
    
    subgraph TestCodeGen
        TruthTableData --> TestFunctionGenerator
        ParsedData --> MockGenerator
        ParsedData --> AssignableVariableChecker
        AssignableVariableChecker --> TestFunctionGenerator
        MockGenerator --> TestCode
        TestFunctionGenerator --> TestCode
    end
    
    subgraph IOTableGen
        TruthTableData --> IOTableGenerator
        ParsedData --> IOTableGenerator
        IOTableGenerator --> IOTableData
    end
    
    subgraph Output
        TruthTableData --> ExcelWriter
        IOTableData --> ExcelWriter
        TestCode --> CTestFile[test_xxx.c]
        ExcelWriter --> TruthTableXlsx[truth_table.xlsx]
        ExcelWriter --> IOTableXlsx[io_table.xlsx]
    end
```

## v4.3.3.1での変更点

### 新規追加
- **AssignableVariableChecker詳細シーケンス**: 代入可能判定の詳細フローを追加
- **TestFunctionGenerator詳細シーケンス**: AssignableVariableCheckerとの連携を追加

### 修正
- TestFunctionGenerator内で`_process_init_code`がAssignableVariableCheckerを使用するフローを追加
