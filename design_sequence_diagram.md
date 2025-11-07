# C言語単体テスト自動生成ツール - シーケンス図

## 1. 全体処理フロー

```mermaid
sequenceDiagram
    actor User
    participant Main as メインプログラム
    participant Parser as CCodeParser
    participant TruthTable as TruthTableGenerator
    participant TestGen as UnityTestGenerator
    participant IOTable as IOTableGenerator
    participant Excel as ExcelWriter

    User->>Main: C言語ファイルを指定
    Main->>Parser: parse(c_file_path)
    
    Note over Parser: C言語ファイルを解析
    Parser->>Parser: プリプロセス処理
    Parser->>Parser: AST生成
    Parser->>Parser: 関数抽出
    Parser->>Parser: 条件分岐抽出
    Parser-->>Main: ParsedData(関数情報, 条件分岐リスト)
    
    Main->>TruthTable: generate(parsed_data)
    Note over TruthTable: MC/DC真偽表を生成
    TruthTable->>TruthTable: if文解析
    TruthTable->>TruthTable: OR/AND条件分解
    TruthTable->>TruthTable: switch-case抽出
    TruthTable->>TruthTable: MC/DCパターン生成
    TruthTable-->>Main: TruthTableData
    
    Main->>Excel: write_truth_table(table_data)
    Excel->>Excel: Excelフォーマット作成
    Excel-->>Main: truth_table.xlsx
    
    Main->>TestGen: generate(truth_table, parsed_data)
    Note over TestGen: Unityテストコード生成
    TestGen->>TestGen: モック/スタブ生成
    TestGen->>TestGen: テスト関数生成
    TestGen->>TestGen: プロトタイプ宣言生成
    TestGen->>TestGen: コメント生成
    TestGen-->>Main: TestCode
    
    Main->>TestGen: save(output_path)
    TestGen-->>Main: test_generated.c
    
    Main->>IOTable: generate(test_code, truth_table)
    Note over IOTable: I/O一覧表を生成
    IOTable->>IOTable: 入力変数抽出
    IOTable->>IOTable: 出力変数抽出
    IOTable->>IOTable: テストケース毎の値設定
    IOTable-->>Main: IOTableData
    
    Main->>Excel: write_io_table(io_table_data)
    Excel-->>Main: io_table.xlsx
    
    Main-->>User: 完了通知（3ファイル生成）
```

## 2. CCodeParser詳細シーケンス

```mermaid
sequenceDiagram
    participant Main as メインプログラム
    participant Parser as CCodeParser
    participant Preprocessor as Preprocessor
    participant ASTBuilder as ASTBuilder
    participant CondExtractor as ConditionExtractor

    Main->>Parser: parse(c_file_path)
    Parser->>Preprocessor: preprocess(c_code)
    
    Note over Preprocessor: プリプロセス処理
    Preprocessor->>Preprocessor: #includeの展開（制限付き）
    Preprocessor->>Preprocessor: #defineの処理
    Preprocessor->>Preprocessor: コメント削除
    Preprocessor-->>Parser: preprocessed_code
    
    Parser->>ASTBuilder: build_ast(preprocessed_code)
    Note over ASTBuilder: pycparserでAST構築
    ASTBuilder->>ASTBuilder: fake_libc_includeを使用
    ASTBuilder->>ASTBuilder: parse_file()
    ASTBuilder-->>Parser: ast
    
    Parser->>CondExtractor: extract_conditions(ast)
    Note over CondExtractor: 条件分岐を抽出
    CondExtractor->>CondExtractor: visit_FuncDef()
    CondExtractor->>CondExtractor: visit_If()
    CondExtractor->>CondExtractor: visit_Switch()
    CondExtractor->>CondExtractor: 条件式の分解
    CondExtractor-->>Parser: conditions_list
    
    Parser-->>Main: ParsedData
```

## 3. TruthTableGenerator詳細シーケンス

```mermaid
sequenceDiagram
    participant Main as メインプログラム
    participant TruthGen as TruthTableGenerator
    participant CondAnalyzer as ConditionAnalyzer
    participant MCDCGen as MCDCPatternGenerator

    Main->>TruthGen: generate(parsed_data)
    
    loop 各条件分岐
        TruthGen->>CondAnalyzer: analyze_condition(cond)
        
        alt 単純if文
            CondAnalyzer->>CondAnalyzer: 条件式解析
            CondAnalyzer-->>TruthGen: {type: "simple", pattern: ["T", "F"]}
        else OR条件
            CondAnalyzer->>CondAnalyzer: 左辺・右辺を分離
            CondAnalyzer->>MCDCGen: generate_or_patterns()
            MCDCGen-->>CondAnalyzer: ["TF", "FT", "FF"]
            CondAnalyzer-->>TruthGen: {type: "or", pattern: ["TF", "FT", "FF"]}
        else AND条件
            CondAnalyzer->>CondAnalyzer: 左辺・右辺を分離
            CondAnalyzer->>MCDCGen: generate_and_patterns()
            MCDCGen-->>CondAnalyzer: ["TF", "FT", "TT"]
            CondAnalyzer-->>TruthGen: {type: "and", pattern: ["TF", "FT", "TT"]}
        else switch文
            CondAnalyzer->>CondAnalyzer: case文を全抽出
            CondAnalyzer-->>TruthGen: {type: "switch", cases: [0,1,2,...]}
        end
    end
    
    TruthGen->>TruthGen: 真偽表データ構築
    TruthGen->>TruthGen: テスト番号採番
    TruthGen-->>Main: TruthTableData
```

## 4. UnityTestGenerator詳細シーケンス

```mermaid
sequenceDiagram
    participant Main as メインプログラム
    participant TestGen as UnityTestGenerator
    participant MockGen as MockGenerator
    participant TestFuncGen as TestFunctionGenerator
    participant CommentGen as CommentGenerator

    Main->>TestGen: generate(truth_table, parsed_data)
    
    TestGen->>MockGen: generate_mocks(parsed_data)
    Note over MockGen: モック/スタブ生成
    MockGen->>MockGen: 外部関数リスト作成
    MockGen->>MockGen: グローバル変数生成
    MockGen->>MockGen: モック関数実装
    MockGen->>MockGen: カウンタ変数追加
    MockGen-->>TestGen: mock_code
    
    loop 各テストケース
        TestGen->>CommentGen: generate_comment(test_case)
        CommentGen->>CommentGen: 対象分岐を記載
        CommentGen->>CommentGen: 条件を記載
        CommentGen->>CommentGen: 期待動作を記載
        CommentGen-->>TestGen: comment_text
        
        TestGen->>TestFuncGen: generate_test_function(test_case)
        TestFuncGen->>TestFuncGen: テスト名生成
        TestFuncGen->>TestFuncGen: 変数初期化コード
        TestFuncGen->>TestFuncGen: モック設定コード
        TestFuncGen->>TestFuncGen: 対象関数呼び出し
        TestFuncGen->>TestFuncGen: TEST_ASSERT_EQUAL生成
        TestFuncGen->>TestFuncGen: 呼び出し回数チェック
        TestFuncGen-->>TestGen: test_function_code
    end
    
    TestGen->>TestGen: プロトタイプ宣言生成
    TestGen->>TestGen: setUp/tearDown生成
    TestGen->>TestGen: 全コードを結合
    TestGen-->>Main: TestCode
```

## 5. データ構造

### ParsedData
```python
{
    'file_name': 'f1_target.c',
    'function_name': 'f1',
    'conditions': [
        {
            'line': 10,
            'type': 'if',
            'expression': '(f4() & 0xdf) != 0',
            'ast_node': <AST Node>
        },
        {
            'line': 15,
            'type': 'if',
            'expression': '(mx63 == m47) || (mx63 == m46)',
            'operator': 'or',
            'left': 'mx63 == m47',
            'right': 'mx63 == m46'
        },
        {
            'line': 25,
            'type': 'switch',
            'expression': 'v9',
            'cases': [0, 1, 2, 3, 4, 5, 6, 7, 'default']
        }
    ],
    'external_functions': ['f4', 'mx27', 'mx52', 'f8', 'f18'],
    'global_variables': ['mx63', 'v7', 'v9', 'v10']
}
```

### TruthTableData
```python
{
    'test_cases': [
        {
            'no': 1,
            'truth': 'T',
            'condition': 'if ((f4() & 0xdf) != 0)',
            'expected': 'v9が7'
        },
        {
            'no': 2,
            'truth': 'F',
            'condition': 'if ((f4() & 0xdf) != 0)',
            'expected': 'v9!=7'
        },
        {
            'no': 3,
            'truth': 'TF',
            'condition': 'if ((mx63 == m47) || (mx63 == m46))',
            'expected': 'mx27()呼び出し'
        }
    ]
}
```
