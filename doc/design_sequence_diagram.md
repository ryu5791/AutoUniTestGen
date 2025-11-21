# AutoUniTestGen シーケンス図 (v2.7)

**最終更新**: 2025-11-20  
**バージョン**: 2.7.0

---

## 概要

このドキュメントでは、AutoUniTestGenの処理フローをシーケンス図で説明します。

v2.7では、以下の改善を予定しています：
- 構造体型戻り値のアサーション生成処理の追加
- 構造体判定ロジックの導入

過去のバージョン履歴：
- v2.6.6: 構造体アサーション問題の識別
- v2.6.5: パラメータ変数型定義追加
- v2.6.4: デフォルト値モック設定の削除
- v2.6.3: コメント形式修正、result変数型定義追加
- v2.6.2: グローバル変数初期化の削除

---

## 全体フロー

```mermaid
sequenceDiagram
    participant User
    participant Main
    participant CLI
    participant CTestAutoGen
    participant CCodeParser
    participant TruthTableGen
    participant UnityTestGen
    participant IOTableGen
    participant ExcelWriter
    
    User->>Main: python main.py -i source.c -f func -o output/
    Main->>CLI: main()
    
    CLI->>CLI: create_parser()
    CLI->>CLI: parse arguments
    CLI->>CTestAutoGen: new(config)
    
    CLI->>CTestAutoGen: generate_all(source.c, func, output/)
    activate CTestAutoGen
    
    CTestAutoGen->>CCodeParser: parse(source.c, func)
    activate CCodeParser
    CCodeParser-->>CTestAutoGen: parsed_data
    deactivate CCodeParser
    
    CTestAutoGen->>TruthTableGen: generate(parsed_data)
    activate TruthTableGen
    TruthTableGen-->>CTestAutoGen: truth_table_data
    deactivate TruthTableGen
    
    CTestAutoGen->>UnityTestGen: generate(truth_table, parsed_data)
    activate UnityTestGen
    UnityTestGen-->>CTestAutoGen: test_code
    deactivate UnityTestGen
    
    CTestAutoGen->>IOTableGen: generate(truth_table, parsed_data)
    activate IOTableGen
    IOTableGen-->>CTestAutoGen: io_table_data
    deactivate IOTableGen
    
    CTestAutoGen->>ExcelWriter: write_truth_table(truth_table_data)
    CTestAutoGen->>ExcelWriter: write_io_table(io_table_data)
    CTestAutoGen->>CTestAutoGen: save test_code to file
    
    CTestAutoGen-->>CLI: generation_result
    deactivate CTestAutoGen
    
    CLI-->>User: ✅ 生成成功
```

---

## 詳細フロー1: ファイル読み込みと前処理

```mermaid
sequenceDiagram
    participant CTestAutoGen
    participant CCodeParser
    participant Preprocessor
    participant FileSystem
    
    CTestAutoGen->>CCodeParser: parse(source_file, target_function)
    activate CCodeParser
    
    CCodeParser->>FileSystem: read file
    FileSystem-->>CCodeParser: source_code
    
    CCodeParser->>Preprocessor: preprocess(source_code)
    activate Preprocessor
    
    Preprocessor->>Preprocessor: remove_comments()
    Preprocessor->>Preprocessor: expand_macros()
    Preprocessor->>Preprocessor: handle_directives()
    Preprocessor->>Preprocessor: resolve_includes()
    
    Preprocessor-->>CCodeParser: preprocessed_code
    deactivate Preprocessor
    
    CCodeParser-->>CTestAutoGen: preprocessed_code
    deactivate CCodeParser
```

---

## 詳細フロー2: 構文解析とAST構築

```mermaid
sequenceDiagram
    participant CCodeParser
    participant ASTBuilder
    participant ConditionExtractor
    participant FunctionExtractor
    participant TypedefExtractor
    participant ParsedData
    
    CCodeParser->>ASTBuilder: build(preprocessed_code)
    activate ASTBuilder
    
    ASTBuilder->>ASTBuilder: parse_with_pycparser()
    alt Parsing Success
        ASTBuilder-->>CCodeParser: ast
    else Parsing Failed
        ASTBuilder->>ASTBuilder: handle_parse_error()
        ASTBuilder->>ASTBuilder: fallback to regex parsing
        ASTBuilder-->>CCodeParser: partial_ast
    end
    deactivate ASTBuilder
    
    CCodeParser->>FunctionExtractor: extract_function_info(ast, target_function)
    activate FunctionExtractor
    FunctionExtractor-->>CCodeParser: function_info
    deactivate FunctionExtractor
    
    CCodeParser->>ConditionExtractor: extract(ast, target_function)
    activate ConditionExtractor
    ConditionExtractor->>ConditionExtractor: visit_if_stmt()
    ConditionExtractor->>ConditionExtractor: visit_switch_stmt()
    ConditionExtractor->>ConditionExtractor: classify_condition_type()
    ConditionExtractor-->>CCodeParser: conditions
    deactivate ConditionExtractor
    
    CCodeParser->>TypedefExtractor: extract_typedefs(ast)
    activate TypedefExtractor
    TypedefExtractor->>TypedefExtractor: parse_typedef_node()
    TypedefExtractor-->>CCodeParser: typedefs
    deactivate TypedefExtractor
    
    Note over CCodeParser,TypedefExtractor: 🆕v2.7: 構造体定義の抽出
    CCodeParser->>TypedefExtractor: extract_struct_definitions(ast)
    activate TypedefExtractor
    TypedefExtractor->>TypedefExtractor: parse_struct_node()
    TypedefExtractor->>TypedefExtractor: extract_struct_members()
    TypedefExtractor-->>CCodeParser: struct_definitions
    deactivate TypedefExtractor
    
    CCodeParser->>ParsedData: new(function_info, conditions, typedefs, struct_definitions)
    ParsedData-->>CCodeParser: parsed_data
    
    CCodeParser-->>CTestAutoGen: parsed_data
```

---

## 詳細フロー3: MC/DC真偽表の生成

```mermaid
sequenceDiagram
    participant CTestAutoGen
    participant TruthTableGen
    participant ConditionAnalyzer
    participant MCDCPatternGen
    participant TruthTableData
    
    CTestAutoGen->>TruthTableGen: generate(parsed_data)
    activate TruthTableGen
    
    TruthTableGen->>ConditionAnalyzer: analyze(conditions)
    activate ConditionAnalyzer
    
    ConditionAnalyzer->>ConditionAnalyzer: analyze_simple_condition()
    ConditionAnalyzer->>ConditionAnalyzer: analyze_compound_condition()
    ConditionAnalyzer->>ConditionAnalyzer: detect_dependencies()
    
    ConditionAnalyzer-->>TruthTableGen: analyzed_conditions
    deactivate ConditionAnalyzer
    
    TruthTableGen->>MCDCPatternGen: generate(analyzed_conditions)
    activate MCDCPatternGen
    
    loop For each condition
        alt Simple IF
            MCDCPatternGen->>MCDCPatternGen: generate_for_simple_if()
        else OR Condition
            MCDCPatternGen->>MCDCPatternGen: generate_for_or_condition()
        else AND Condition
            MCDCPatternGen->>MCDCPatternGen: generate_for_and_condition()
        else SWITCH
            MCDCPatternGen->>MCDCPatternGen: generate_for_switch()
        end
        
        MCDCPatternGen->>MCDCPatternGen: calculate_mcdc_pairs()
    end
    
    MCDCPatternGen-->>TruthTableGen: test_cases
    deactivate MCDCPatternGen
    
    TruthTableGen->>TruthTableData: new(function_name, test_cases)
    TruthTableData-->>TruthTableGen: truth_table_data
    
    TruthTableGen-->>CTestAutoGen: truth_table_data
    deactivate TruthTableGen
```

---

## 詳細フロー4: Unityテストコードの生成

```mermaid
sequenceDiagram
    participant CTestAutoGen
    participant UnityTestGen
    participant MockGen
    participant TestFuncGen
    participant ProtoGen
    participant CommentGen
    participant CodeExtractor
    participant TestCode
    
    CTestAutoGen->>UnityTestGen: generate(truth_table, parsed_data, source)
    activate UnityTestGen
    
    UnityTestGen->>UnityTestGen: _generate_includes()
    UnityTestGen->>UnityTestGen: _generate_type_definitions(parsed_data)
    
    UnityTestGen->>ProtoGen: generate_prototypes(parsed_data)
    activate ProtoGen
    ProtoGen-->>UnityTestGen: prototypes
    deactivate ProtoGen
    
    UnityTestGen->>MockGen: generate_mocks(parsed_data)
    activate MockGen
    MockGen->>MockGen: generate_mock_variables()
    MockGen->>MockGen: generate_mock_functions()
    MockGen->>MockGen: generate_reset_function()
    MockGen-->>UnityTestGen: mocks
    deactivate MockGen
    
    UnityTestGen->>TestFuncGen: generate_test_functions(truth_table, parsed_data)
    activate TestFuncGen
    
    loop For each test_case in truth_table
        TestFuncGen->>TestFuncGen: _generate_test_function(test_case)
        TestFuncGen->>CommentGen: generate_test_comment(test_case)
        activate CommentGen
        CommentGen-->>TestFuncGen: comment
        deactivate CommentGen
        
        TestFuncGen->>TestFuncGen: _generate_function_name()
        TestFuncGen->>TestFuncGen: _generate_variable_init()
        TestFuncGen->>TestFuncGen: _generate_mock_setup()
        TestFuncGen->>TestFuncGen: _generate_function_call()
        
        Note over TestFuncGen: 🆕v2.7: 構造体型対応
        TestFuncGen->>TestFuncGen: _generate_assertions(test_case, parsed_data)
        activate TestFuncGen
        
        alt return_type is struct
            TestFuncGen->>TestFuncGen: _is_struct_type(return_type)
            TestFuncGen->>TestFuncGen: _get_struct_members(return_type, parsed_data)
            TestFuncGen->>TestFuncGen: generate TODO comment
        else return_type is basic
            TestFuncGen->>TestFuncGen: generate TEST_ASSERT_EQUAL
        end
        
        deactivate TestFuncGen
    end
    
    TestFuncGen-->>UnityTestGen: test_functions
    deactivate TestFuncGen
    
    UnityTestGen->>UnityTestGen: _generate_setup_teardown()
    
    UnityTestGen->>CodeExtractor: extract_function_body(source)
    activate CodeExtractor
    CodeExtractor-->>UnityTestGen: target_function_code
    deactivate CodeExtractor
    
    UnityTestGen->>UnityTestGen: _generate_main_function(truth_table)
    
    UnityTestGen->>TestCode: new(includes, mocks, test_functions, ...)
    TestCode-->>UnityTestGen: test_code
    
    UnityTestGen-->>CTestAutoGen: test_code
    deactivate UnityTestGen
```

---

## 詳細フロー5: テスト関数の生成（構造体対応） 🆕v2.7

```mermaid
sequenceDiagram
    participant TestFuncGen as TestFunctionGenerator
    participant ParsedData
    participant StructDef as StructDefinition
    
    Note over TestFuncGen: テスト関数生成開始
    
    TestFuncGen->>TestFuncGen: _generate_function_name(test_case)
    TestFuncGen->>TestFuncGen: _generate_variable_init(test_case, parsed_data)
    
    Note over TestFuncGen: 戻り値の型をチェック
    TestFuncGen->>TestFuncGen: get return_type from parsed_data.function_info
    
    alt return_type is void
        TestFuncGen->>TestFuncGen: skip result variable
    else return_type is not void
        TestFuncGen->>TestFuncGen: _is_struct_type(return_type)
        
        alt is struct type
            Note over TestFuncGen: 構造体の場合
            TestFuncGen->>TestFuncGen: generate: {return_type} result = {0};
            
            TestFuncGen->>TestFuncGen: _generate_assertions()
            activate TestFuncGen
            
            TestFuncGen->>ParsedData: get struct_definitions
            ParsedData-->>TestFuncGen: struct_definitions
            
            TestFuncGen->>TestFuncGen: find struct by return_type
            
            alt struct members found
                TestFuncGen->>StructDef: get members
                StructDef-->>TestFuncGen: List[StructMember]
                
                loop For each member
                    TestFuncGen->>TestFuncGen: generate: TEST_ASSERT_EQUAL(0, result.{member});
                end
            else struct members not found
                TestFuncGen->>TestFuncGen: generate TODO comment
                Note right of TestFuncGen: // TODO: 構造体のメンバーごとに<br/>期待値を設定してください<br/>// 例: TEST_ASSERT_EQUAL(expected, result.member);
            end
            
            deactivate TestFuncGen
            
        else is basic type
            Note over TestFuncGen: 基本型の場合
            TestFuncGen->>TestFuncGen: generate: {return_type} result = 0;
            TestFuncGen->>TestFuncGen: generate: TEST_ASSERT_EQUAL(0, result);
        end
    end
    
    TestFuncGen->>TestFuncGen: combine all sections
    TestFuncGen-->>TestFuncGen: complete test function
```

---

## 詳細フロー6: I/O表の生成

```mermaid
sequenceDiagram
    participant CTestAutoGen
    participant IOTableGen
    participant VariableExtractor
    participant IOTableData
    
    CTestAutoGen->>IOTableGen: generate(truth_table, parsed_data)
    activate IOTableGen
    
    IOTableGen->>VariableExtractor: extract_io_variables(parsed_data)
    activate VariableExtractor
    
    VariableExtractor->>VariableExtractor: extract_input_variables()
    VariableExtractor->>VariableExtractor: extract_output_variables()
    VariableExtractor->>VariableExtractor: classify_variable_roles()
    
    VariableExtractor-->>IOTableGen: io_variables
    deactivate VariableExtractor
    
    loop For each test_case in truth_table
        IOTableGen->>IOTableGen: map_test_case_to_io(test_case, io_variables)
        IOTableGen->>IOTableGen: infer_input_values(test_case)
        IOTableGen->>IOTableGen: infer_output_values(test_case)
    end
    
    IOTableGen->>IOTableData: new(function_name, io_variables, test_entries)
    IOTableData-->>IOTableGen: io_table_data
    
    IOTableGen-->>CTestAutoGen: io_table_data
    deactivate IOTableGen
```

---

## 詳細フロー7: Excelファイルの出力

```mermaid
sequenceDiagram
    participant CTestAutoGen
    participant ExcelWriter
    participant openpyxl
    participant FileSystem
    
    CTestAutoGen->>ExcelWriter: write_truth_table(truth_table_data, path)
    activate ExcelWriter
    
    ExcelWriter->>openpyxl: Workbook()
    openpyxl-->>ExcelWriter: workbook
    
    ExcelWriter->>ExcelWriter: create_worksheet("真偽表")
    ExcelWriter->>ExcelWriter: format_header_row()
    
    loop For each test_case
        ExcelWriter->>ExcelWriter: format_data_row(test_case)
    end
    
    ExcelWriter->>openpyxl: save(path)
    openpyxl->>FileSystem: write file
    
    ExcelWriter-->>CTestAutoGen: success
    deactivate ExcelWriter
    
    CTestAutoGen->>ExcelWriter: write_io_table(io_table_data, path)
    activate ExcelWriter
    
    ExcelWriter->>openpyxl: Workbook()
    openpyxl-->>ExcelWriter: workbook
    
    ExcelWriter->>ExcelWriter: create_worksheet("I/O一覧")
    ExcelWriter->>ExcelWriter: format_header_row()
    
    loop For each io_entry
        ExcelWriter->>ExcelWriter: format_data_row(io_entry)
    end
    
    ExcelWriter->>openpyxl: save(path)
    openpyxl->>FileSystem: write file
    
    ExcelWriter-->>CTestAutoGen: success
    deactivate ExcelWriter
```

---

## バッチ処理フロー

```mermaid
sequenceDiagram
    participant User
    participant CLI
    participant BatchProcessor
    participant CTestAutoGen
    participant ThreadPool
    
    User->>CLI: python main.py --batch config.json --parallel --workers 4
    CLI->>CLI: parse arguments
    CLI->>BatchProcessor: new(config)
    
    CLI->>BatchProcessor: process_batch(config.json)
    activate BatchProcessor
    
    BatchProcessor->>BatchProcessor: load_batch_config()
    BatchProcessor->>BatchProcessor: validate_tasks()
    
    alt Parallel Mode
        BatchProcessor->>ThreadPool: create pool (workers=4)
        
        loop For each task
            BatchProcessor->>ThreadPool: submit(process_single, task)
        end
        
        loop For each future
            ThreadPool->>CTestAutoGen: generate_all(...)
            CTestAutoGen-->>ThreadPool: result
            ThreadPool-->>BatchProcessor: result
        end
        
    else Sequential Mode
        loop For each task
            BatchProcessor->>CTestAutoGen: generate_all(...)
            CTestAutoGen-->>BatchProcessor: result
        end
    end
    
    BatchProcessor->>BatchProcessor: aggregate_results()
    BatchProcessor-->>CLI: List[GenerationResult]
    deactivate BatchProcessor
    
    CLI-->>User: ✅ バッチ処理完了
```

---

## エラーハンドリングフロー

```mermaid
sequenceDiagram
    participant Component
    participant ErrorHandler
    participant Logger
    participant User
    
    Component->>Component: execute operation
    
    alt Operation Failed
        Component->>ErrorHandler: handle_error(error, level)
        activate ErrorHandler
        
        ErrorHandler->>ErrorHandler: format_error_message(error)
        ErrorHandler->>ErrorHandler: determine_severity(level)
        
        ErrorHandler->>Logger: log(message, level)
        activate Logger
        Logger->>Logger: write to log file
        Logger-->>ErrorHandler: logged
        deactivate Logger
        
        alt Critical Error
            ErrorHandler->>ErrorHandler: prepare detailed report
            ErrorHandler-->>User: ❌ Critical Error: {details}
        else Warning
            ErrorHandler-->>User: ⚠️ Warning: {message}
        else Info
            ErrorHandler-->>User: ℹ️ Info: {message}
        end
        
        ErrorHandler-->>Component: error handled
        deactivate ErrorHandler
    end
```

---

## パフォーマンス監視フロー

```mermaid
sequenceDiagram
    participant CLI
    participant PerfMonitor as PerformanceMonitor
    participant MemMonitor as MemoryMonitor
    participant CTestAutoGen
    
    CLI->>PerfMonitor: start_timer("total")
    CLI->>MemMonitor: log_memory_snapshot("start")
    
    CLI->>CTestAutoGen: generate_all(...)
    activate CTestAutoGen
    
    CTestAutoGen->>PerfMonitor: start_timer("parsing")
    Note over CTestAutoGen: Parsing...
    CTestAutoGen->>PerfMonitor: stop_timer("parsing")
    
    CTestAutoGen->>PerfMonitor: start_timer("truth_table")
    Note over CTestAutoGen: Truth table generation...
    CTestAutoGen->>PerfMonitor: stop_timer("truth_table")
    
    CTestAutoGen->>PerfMonitor: start_timer("test_generation")
    Note over CTestAutoGen: Test generation...
    CTestAutoGen->>PerfMonitor: stop_timer("test_generation")
    
    CTestAutoGen-->>CLI: result
    deactivate CTestAutoGen
    
    CLI->>PerfMonitor: stop_timer("total")
    CLI->>MemMonitor: log_memory_snapshot("end")
    
    CLI->>PerfMonitor: get_metrics()
    PerfMonitor-->>CLI: metrics
    
    CLI->>MemMonitor: get_peak_memory()
    MemMonitor-->>CLI: peak_memory
    
    CLI->>CLI: display performance report
    CLI-->>User: Performance Report:<br/>- Total: 2.5s<br/>- Parsing: 0.5s<br/>- Truth Table: 0.8s<br/>- Test Gen: 1.2s<br/>- Peak Memory: 150MB
```

---

## v2.7での主要な変更点

### 構造体型アサーション生成フロー（新規追加）

v2.7では、`TestFunctionGenerator._generate_assertions()`メソッドに以下の処理が追加されます：

1. **戻り値の型チェック**
   - `parsed_data.function_info.return_type`を取得
   
2. **構造体判定**
   - `_is_struct_type(return_type)`を呼び出し
   - 型名から構造体かどうかを判定
   
3. **構造体の場合の処理**
   - `parsed_data.struct_definitions`から構造体定義を検索
   - メンバー情報が取得できた場合：
     - 各メンバーごとに`TEST_ASSERT_EQUAL`を生成
   - メンバー情報が取得できない場合：
     - TODOコメントを生成
   
4. **基本型の場合の処理**
   - 従来通りのアサーション生成

### データフロー変更

```
TypedefExtractor
    ↓ (v2.7で追加)
extract_struct_definitions()
    ↓
StructDefinition[] → ParsedData
    ↓
UnityTestGenerator
    ↓
TestFunctionGenerator
    ↓
_generate_assertions()
    ↓
_is_struct_type() → bool
    ↓
_get_struct_members() → List[StructMember]
    ↓
generate assertions or TODO comments
```

---

## 主要な処理時間の目安

| フェーズ | 処理時間 | 備考 |
|---------|---------|------|
| ファイル読み込み | 10-50ms | ファイルサイズに依存 |
| 前処理 | 50-200ms | マクロ展開、コメント除去 |
| AST構築 | 100-500ms | コードの複雑さに依存 |
| 条件抽出 | 50-200ms | 条件分岐の数に依存 |
| 真偽表生成 | 200-1000ms | MC/DCパターン計算 |
| テスト生成 | 300-1500ms | テストケース数に依存 |
| Excel出力 | 100-300ms | データ量に依存 |
| **合計** | **0.8-3.8秒** | 標準的なケース |

---

## 設計の特徴

1. **レイヤー化されたアーキテクチャ**: 各レイヤーが独立して動作
2. **依存性の注入**: コンポーネント間の疎結合
3. **エラーハンドリングの一元化**: ErrorHandlerによる集中管理
4. **段階的な処理**: 各ステップが明確に分離
5. **拡張性**: 新機能（構造体対応など）が追加しやすい構造

---

**作成日**: 2025-11-20  
**作成者**: AutoUniTestGen Development Team  
**バージョン**: 2.7.0  
**状態**: ✅ 最新
