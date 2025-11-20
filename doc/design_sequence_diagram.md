# C言語単体テスト自動生成ツール - シーケンス図 v2.6.0

**更新日**: 2025-11-19  
**バージョン**: v2.6.0  
**主な変更**: ネストしたAND/OR条件のMC/DC処理フロー追加

---

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
    Parser->>Parser: 条件分岐抽出（ネスト対応）
    Parser-->>Main: ParsedData(関数情報, 条件分岐リスト)
    
    Main->>TruthTable: generate(parsed_data)
    Note over TruthTable: MC/DC真偽表を生成（v2.6.0拡張）
    TruthTable->>TruthTable: if文解析
    TruthTable->>TruthTable: ネスト構造検出
    TruthTable->>TruthTable: OR/AND条件再帰展開
    TruthTable->>TruthTable: switch-case抽出
    TruthTable->>TruthTable: MC/DCパターン生成（100%）
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

---

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
    CondExtractor->>CondExtractor: _analyze_binary_op()
    CondExtractor->>CondExtractor: _extract_all_conditions()
    Note over CondExtractor: v2.6.0: ネスト条件を再帰的に抽出
    CondExtractor-->>Parser: conditions_list
    
    Parser-->>Main: ParsedData
```

---

## 3. TruthTableGenerator詳細シーケンス（v2.6.0拡張）

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
        
        else OR条件（シンプル）
            CondAnalyzer->>CondAnalyzer: 条件数を確認
            CondAnalyzer->>MCDCGen: generate_or_patterns(n)
            MCDCGen-->>CondAnalyzer: ["TF", "FT", "FF"]
            CondAnalyzer-->>TruthGen: {type: "or", pattern: [...]}
        
        else AND条件（シンプル）
            CondAnalyzer->>CondAnalyzer: 条件数を確認
            CondAnalyzer->>MCDCGen: generate_and_patterns(n)
            MCDCGen-->>CondAnalyzer: ["TF", "FT", "TT"]
            CondAnalyzer-->>TruthGen: {type: "and", pattern: [...]}
        
        else ネストしたAND条件 (v2.6.0)
            CondAnalyzer->>CondAnalyzer: ネスト構造を検出
            Note over CondAnalyzer: has_nested = True
            CondAnalyzer->>MCDCGen: generate_mcdc_patterns_for_complex('and', conditions)
            
            Note over MCDCGen: 新機能: 複雑条件の処理
            MCDCGen->>MCDCGen: _extract_or_conditions() 再帰的展開
            MCDCGen->>MCDCGen: _extract_and_conditions() 再帰的展開
            MCDCGen->>MCDCGen: 構造情報を構築
            Note over MCDCGen: structure = [('simple',1), ('or',6), ('simple',1)]
            
            MCDCGen->>MCDCGen: _generate_patterns_for_structure()
            
            loop 各条件グループ
                alt ORグループ
                    MCDCGen->>MCDCGen: _generate_or_group_patterns_with_structure()
                    Note over MCDCGen: 各OR条件を1つずつTrueに
                else 単純条件
                    MCDCGen->>MCDCGen: _generate_simple_condition_patterns_with_structure()
                    Note over MCDCGen: 独立性テストパターン生成
                end
            end
            
            MCDCGen->>MCDCGen: 重複パターンを削除
            MCDCGen-->>CondAnalyzer: ["TTFFFFFT", "FTFFFFFT", ...]
            Note over MCDCGen: MC/DC 100%のパターン
            CondAnalyzer-->>TruthGen: {type: "and", pattern: [...], has_nested: true}
        
        else ネストしたOR条件 (v2.6.0)
            CondAnalyzer->>CondAnalyzer: ネスト構造を検出
            CondAnalyzer->>MCDCGen: generate_mcdc_patterns_for_complex('or', conditions)
            MCDCGen->>MCDCGen: 再帰的展開とパターン生成
            MCDCGen-->>CondAnalyzer: MC/DCパターン
            CondAnalyzer-->>TruthGen: {type: "or", pattern: [...], has_nested: true}
        
        else switch文
            CondAnalyzer->>CondAnalyzer: case文を全抽出
            CondAnalyzer-->>TruthGen: {type: "switch", cases: [0,1,2,...]}
        end
    end
    
    TruthGen->>TruthGen: 真偽表データ構築
    TruthGen->>TruthGen: テスト番号採番
    TruthGen-->>Main: TruthTableData
```

---

## 4. MCDCPatternGenerator詳細シーケンス（v2.6.0新規）

```mermaid
sequenceDiagram
    participant Analyzer as ConditionAnalyzer
    participant MCDC as MCDCPatternGenerator
    participant Extractor as 条件展開メソッド
    participant Generator as パターン生成メソッド

    Analyzer->>MCDC: generate_mcdc_patterns_for_complex('and', conditions)
    
    Note over MCDC: Step 1: 条件を展開
    loop 各条件
        MCDC->>MCDC: 条件の種類を判定
        
        alt OR条件を含む
            MCDC->>Extractor: _extract_or_conditions(cond)
            Extractor->>Extractor: 外側の括弧を削除
            Extractor->>Extractor: ORで分割
            
            loop 各パーツ
                alt パーツにORが残っている
                    Extractor->>Extractor: 再帰的に_extract_or_conditions()
                    Note over Extractor: ネスト構造を完全展開
                end
            end
            
            Extractor-->>MCDC: [cond1, cond2, ..., condN]
        
        else AND条件を含む
            MCDC->>Extractor: _extract_and_conditions(cond)
            Extractor->>Extractor: 再帰的にAND展開
            Extractor-->>MCDC: [cond1, cond2, ..., condN]
        
        else 単純条件
            MCDC->>MCDC: そのまま追加
        end
        
        MCDC->>MCDC: 構造情報を記録
        Note over MCDC: structure.append((type, count))
    end
    
    Note over MCDC: Step 2: パターン生成
    MCDC->>Generator: _generate_patterns_for_structure(structure)
    
    loop 各条件グループ
        alt ORグループ
            Generator->>Generator: _generate_or_group_patterns_with_structure()
            Note over Generator: パターン1: 全てFalse
            Note over Generator: パターン2-N: 各条件を1つずつTrue
            Generator->>Generator: ベースパターンを作成
            Note over Generator: _create_base_pattern_for_and()
        
        else AND条件
            Generator->>Generator: _generate_and_group_patterns()
            Note over Generator: 各条件を1つずつFalse
        
        else 単純条件
            Generator->>Generator: _generate_simple_condition_patterns_with_structure()
            Note over Generator: 独立性テストのペア
        end
        
        Generator->>Generator: パターンをSetに追加
        Note over Generator: 重複を自動除去
    end
    
    Generator-->>MCDC: patterns_set
    
    MCDC->>MCDC: パターンをソート
    MCDC->>MCDC: 文字列に変換
    Note over MCDC: ["TTFFFFFT", "FTFFFFFT", ...]
    
    MCDC-->>Analyzer: MC/DCパターンリスト
```

---

## 5. UnityTestGenerator詳細シーケンス

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
        CommentGen->>CommentGen: 真偽パターンを記載
        Note over CommentGen: v2.6.0: ネスト条件も詳細に
        CommentGen->>CommentGen: 期待動作を記載
        CommentGen-->>TestGen: comment_text
        
        TestGen->>TestFuncGen: generate_test_function(test_case)
        TestFuncGen->>TestFuncGen: テスト名生成
        TestFuncGen->>TestFuncGen: 変数初期化コード
        Note over TestFuncGen: v2.6.0: ネスト条件対応
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

---

## 6. IOTableGenerator詳細シーケンス

```mermaid
sequenceDiagram
    participant Main as メインプログラム
    participant IOTable as IOTableGenerator
    participant VarExtractor as VariableExtractor

    Main->>IOTable: generate(test_code, truth_table)
    
    IOTable->>VarExtractor: extract_input_variables(test_code)
    Note over VarExtractor: テストコードから入力変数を抽出
    VarExtractor->>VarExtractor: 代入文を解析
    VarExtractor->>VarExtractor: モック設定を解析
    VarExtractor-->>IOTable: input_variables_list
    
    IOTable->>VarExtractor: extract_output_variables(test_code)
    Note over VarExtractor: 出力変数を抽出
    VarExtractor->>VarExtractor: TEST_ASSERT文を解析
    VarExtractor->>VarExtractor: 期待値を取得
    VarExtractor-->>IOTable: output_variables_list
    
    loop 各テストケース
        IOTable->>IOTable: テストケース番号を設定
        IOTable->>IOTable: 入力値を設定
        Note over IOTable: v2.6.0: ネスト条件の真偽値も反映
        IOTable->>IOTable: 期待出力値を設定
        IOTable->>IOTable: I/O表データに追加
    end
    
    IOTable-->>Main: IOTableData
```

---

## 7. v2.6.0の主要な処理フロー（ネスト条件）

```mermaid
sequenceDiagram
    participant User
    participant System as AutoUniTestGen
    participant MCDC as MCDCパターン生成

    User->>System: ネスト条件のCコード
    Note over User: if ((A) && ((B||C||D||E||F||G)) && (H))
    
    System->>System: 条件抽出
    Note over System: conditions = ["A", "((B||C||D||E||F||G))", "H"]
    
    System->>System: ネスト構造検出
    Note over System: has_nested = True
    
    System->>MCDC: 複雑条件処理開始
    
    MCDC->>MCDC: 再帰的展開
    Note over MCDC: Step 1: OR条件を展開
    Note over MCDC: "((B||C||D||E||F||G))" → ["B","C","D","E","F","G"]
    
    MCDC->>MCDC: 構造情報構築
    Note over MCDC: structure = [<br/>('simple', 1),  # A<br/>('or', 6),      # B-G<br/>('simple', 1)   # H<br/>]
    
    MCDC->>MCDC: MC/DCパターン生成
    Note over MCDC: Step 2a: Aの独立性テスト<br/>TTFFFFFT vs FTFFFFFT
    Note over MCDC: Step 2b: B-Gの各独立性テスト<br/>TFFFFFFT vs TFTFFFFT<br/>TFFFFFFT vs TFFTFFFT<br/>... (6パターン)
    Note over MCDC: Step 2c: Hの独立性テスト<br/>TTFFFFFT vs TTFFFFFF
    
    MCDC->>MCDC: 重複削除
    Note over MCDC: 9個のユニークパターン
    
    MCDC-->>System: MC/DCパターン（100%）
    System-->>User: 真偽表Excel（9パターン）
```

---

## 8. データ構造

### ParsedData（拡張版）
```python
{
    'file_name': 'sample.c',
    'function_name': 'process',
    'conditions': [
        {
            'line': 10,
            'type': 'and_condition',
            'expression': '((A) && ((B||C||D||E||F||G)) && (H))',
            'operator': 'and',
            'conditions': [  # v2.6.0: 展開された条件リスト
                '(A)',
                '((B||C||D||E||F||G))',
                '(H)'
            ],
            'has_nested': True,  # v2.6.0: ネスト構造フラグ
            'ast_node': <AST Node>
        }
    ],
    'external_functions': ['f4', 'mx27'],
    'global_variables': ['sensor', 'mode', 'status']
}
```

### TruthTableData（拡張版）
```python
{
    'test_cases': [
        {
            'no': 1,
            'truth': 'TTFFFFFT',  # v2.6.0: 8桁（展開後の条件数）
            'condition': 'if ((A) && ((B||C||D||E||F||G)) && (H))',
            'expected': '条件を満たす',
            'pattern_explanation': 'A=T, B=T(他F), H=T'  # v2.6.0: 詳細説明
        },
        {
            'no': 2,
            'truth': 'FTFFFFFT',
            'condition': 'if ((A) && ((B||C||D||E||F||G)) && (H))',
            'expected': '条件を満たさない',
            'pattern_explanation': 'A=F(独立性), B=T, H=T'
        },
        # ... 9パターン
    ]
}
```

---

## 変更履歴

### v2.6.0 (2025-11-19)
- ✅ ネストしたAND/OR条件の処理フロー追加
- ✅ MCDCPatternGeneratorの詳細シーケンス追加
- ✅ 再帰的展開のフロー図追加
- ✅ MC/DC 100%カバレッジの処理プロセス明確化

### v2.5.0以前
- 基本的な処理フロー
- 単純なOR/AND条件のみ対応

---

**注**: このシーケンス図は、v2.6.0で実装されたネストしたAND/OR条件のMC/DC処理を正確に反映しています。
