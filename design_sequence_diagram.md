# C言語単体テスト自動生成ツール - シーケンス図（関数マクロ対応版）

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
    Parser->>Parser: プリプロセス処理<br/>（関数マクロ展開含む）
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

## 2. CCodeParser詳細シーケンス（関数マクロ対応版）

```mermaid
sequenceDiagram
    participant Main as メインプログラム
    participant Parser as CCodeParser
    participant Preprocessor as Preprocessor
    participant ASTBuilder as ASTBuilder
    participant CondExtractor as ConditionExtractor

    Main->>Parser: parse(c_file_path, defines)
    Parser->>Preprocessor: preprocess(c_code)
    
    Note over Preprocessor: プリプロセス処理<br/>（関数マクロ対応）
    
    Preprocessor->>Preprocessor: _collect_defines(code)<br/>通常マクロと関数マクロを検出
    Note right of Preprocessor: #define MAX(a,b) ...<br/>#define THRESHOLD 100
    
    Preprocessor->>Preprocessor: _process_conditional_compilation(code)<br/>#ifdef/#ifndef/#if処理
    
    Preprocessor->>Preprocessor: _expand_function_macros(code)<br/>関数マクロを展開（最大10回反復）
    Note right of Preprocessor: MAX(10, 20) →<br/>((10) > (20) ? (10) : (20))
    
    Preprocessor->>Preprocessor: _expand_macros(code)<br/>通常マクロを展開
    Note right of Preprocessor: THRESHOLD → 100
    
    Preprocessor->>Preprocessor: _handle_includes(code)<br/>#includeをコメント化
    
    Preprocessor->>Preprocessor: _process_remaining_directives(code)<br/>#pragma等を処理
    
    Preprocessor->>Preprocessor: _remove_comments(code)<br/>コメント削除
    
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

## 3. Preprocessor - 関数マクロ展開詳細シーケンス（NEW!）

```mermaid
sequenceDiagram
    participant Preprocessor
    participant Collector as _collect_defines
    participant Expander as _expand_function_macros
    participant SingleExpander as _expand_single_function_macro
    participant Parser as _parse_macro_arguments

    Preprocessor->>Collector: _collect_defines(code)
    
    loop 各行をスキャン
        Collector->>Collector: 通常マクロ検出<br/>#define MAX 100
        Collector->>Collector: 関数マクロ検出<br/>#define MAX(a,b) ((a)>(b)?(a):(b))
        Note right of Collector: 正規表現で<br/>引数リストを抽出
        Collector->>Collector: defines辞書に追加<br/>function_macros辞書に追加
    end
    
    Collector-->>Preprocessor: defines, function_macros
    
    Preprocessor->>Expander: _expand_function_macros(code)
    
    loop 最大10回反復（ネスト対応）
        loop 各関数マクロ
            Expander->>SingleExpander: _expand_single_function_macro(code, macro_name, params, body)
            
            loop コードをスキャン
                alt マクロ呼び出し検出
                    SingleExpander->>SingleExpander: _extract_balanced_parentheses()<br/>括弧のバランスを考慮して引数を抽出
                    Note right of SingleExpander: MAX(a+b, c-d)<br/>括弧内の括弧も考慮
                    
                    SingleExpander->>Parser: _parse_macro_arguments(args_str)
                    Note right of Parser: カンマで分割<br/>括弧の深さを考慮
                    Parser-->>SingleExpander: args_list
                    
                    alt 引数数が一致
                        SingleExpander->>SingleExpander: パラメータを引数で置換<br/>単語境界を考慮
                        Note right of SingleExpander: (a) → (a+b)<br/>(b) → (c-d)
                    else 引数数不一致
                        SingleExpander->>SingleExpander: 警告を出力<br/>展開せず元のまま
                    end
                end
            end
            
            SingleExpander-->>Expander: expanded_code
        end
        
        alt コードに変化なし
            Note over Expander: 展開完了
            break
        end
    end
    
    alt 最大反復回数に到達
        Expander->>Expander: 循環参照の警告
    end
    
    Expander-->>Preprocessor: fully_expanded_code
```

## 4. 関数マクロ展開の具体例

### 例1: 基本的な関数マクロ

```
入力コード:
#define MAX(a, b)  ((a) > (b) ? (a) : (b))
int result = MAX(10, 20);

展開後:
int result = ((10) > (20) ? (10) : (20));
```

### 例2: ネストした関数マクロ（3段階）

```
入力コード:
#define ABS(x)  ((x) < 0 ? -(x) : (x))
#define DIFF(a, b)  ABS((a) - (b))
#define IN_RANGE(val, center, tolerance)  (DIFF((val), (center)) <= (tolerance))
if (IN_RANGE(10, 5, 3)) { ... }

展開過程:
1回目: IN_RANGE(10, 5, 3) → (DIFF((10), (5)) <= (3))
2回目: DIFF((10), (5)) → ABS(((10)) - ((5)))
3回目: ABS(((10)) - ((5))) → ((((10)) - ((5))) < 0 ? -(((10)) - ((5))) : (((10)) - ((5))))

最終展開後:
if ((((((10)) - ((5))) < 0 ? -(((10)) - ((5))) : (((10)) - ((5)))) <= (3))) { ... }
```

### 例3: 複雑な引数を含む関数マクロ

```
入力コード:
#define CLAMP(val, min, max)  ((val) < (min) ? (min) : ((val) > (max) ? (max) : (val)))
int result = CLAMP(x + y, 0, 100);

展開後:
int result = (((x + y)) < (0) ? (0) : (((x + y)) > (100) ? (100) : (x + y)));
```

## 5. TruthTableGenerator詳細シーケンス

```mermaid
sequenceDiagram
    participant Main as メインプログラム
    participant TruthGen as TruthTableGenerator
    participant CondAnalyzer as ConditionAnalyzer
    participant MCDCGen as MCDCPatternGenerator

    Main->>TruthGen: generate(parsed_data)
    Note over TruthGen: 関数マクロ展開済みの<br/>条件式を処理
    
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

## 6. UnityTestGenerator詳細シーケンス

```mermaid
sequenceDiagram
    participant Main as メインプログラム
    participant TestGen as UnityTestGenerator
    participant MockGen as MockGenerator
    participant TestFuncGen as TestFunctionGenerator
    participant CommentGen as CommentGenerator

    Main->>TestGen: generate(truth_table, parsed_data)
    
    TestGen->>MockGen: generate_mocks(parsed_data)
    Note over MockGen: モック/スタブ生成<br/>（マクロ展開済みコードに基づく）
    MockGen->>MockGen: 外部関数リスト作成
    MockGen->>MockGen: グローバル変数生成
    MockGen->>MockGen: モック関数実装
    MockGen->>MockGen: カウンタ変数追加
    MockGen-->>TestGen: mock_code
    
    loop 各テストケース
        TestGen->>CommentGen: generate_comment(test_case)
        CommentGen->>CommentGen: 対象分岐を記載
        CommentGen->>CommentGen: 条件を記載<br/>（展開後の式を含む）
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

## 7. データ構造（関数マクロ対応版）

### ParsedData（更新）
```python
{
    'file_name': 'f1_target.c',
    'function_name': 'f1',
    'conditions': [
        {
            'line': 10,
            'type': 'if',
            'expression': '(f4() & 0xdf) != 0',  # マクロ展開済み
            'ast_node': <AST Node>
        },
        {
            'line': 15,
            'type': 'if',
            # 元: if (MAX(a, b) > threshold)
            # 展開後: if (((a) > (b) ? (a) : (b)) > threshold)
            'expression': '(((a) > (b) ? (a) : (b)) > threshold)',
            'operator': 'gt',
            'left': '((a) > (b) ? (a) : (b))',
            'right': 'threshold'
        }
    ],
    'external_functions': ['f4'],
    'global_variables': ['a', 'b', 'threshold'],
    'macros_info': {  # NEW!
        'defines': {
            'THRESHOLD': '100',
            'OFFSET': '10'
        },
        'function_macros': {
            'MAX': (['a', 'b'], '((a) > (b) ? (a) : (b))'),
            'MIN': (['a', 'b'], '((a) < (b) ? (a) : (b))')
        }
    }
}
```

### Preprocessor内部データ構造（NEW!）
```python
class Preprocessor:
    defines: Dict[str, str] = {
        'MAX_SIZE': '100',
        'THRESHOLD': '50'
    }
    
    function_macros: Dict[str, Tuple[List[str], str]] = {
        'MAX': (['a', 'b'], '((a) > (b) ? (a) : (b))'),
        'CLAMP': (['val', 'min', 'max'], 
                  '((val) < (min) ? (min) : ((val) > (max) ? (max) : (val)))')
    }
```

## 8. エラーハンドリングシーケンス（関数マクロ）

```mermaid
sequenceDiagram
    participant Code as ソースコード
    participant Preprocessor
    participant Logger

    Code->>Preprocessor: MACRO(arg1, arg2, arg3)
    
    alt 引数数が一致しない
        Preprocessor->>Logger: WARNING: 引数数不一致<br/>期待=2, 実際=3
        Preprocessor->>Preprocessor: 元のコードを維持（展開しない）
    else 括弧が閉じていない
        Preprocessor->>Preprocessor: 元のコードを維持
        Note over Preprocessor: pycparserで<br/>構文エラー検出
    else 循環参照検出
        Preprocessor->>Logger: WARNING: 循環参照の可能性<br/>最大反復回数到達
        Preprocessor->>Preprocessor: 部分展開結果を使用
    else 正常展開
        Preprocessor->>Preprocessor: マクロを完全展開
    end
    
    Preprocessor-->>Code: 処理済みコード
```

## 9. パフォーマンス最適化シーケンス

```mermaid
sequenceDiagram
    participant Main
    participant Cache as ResultCache
    participant Preprocessor
    participant Parser as CCodeParser

    Main->>Cache: get_cached_result(file_path, function)
    
    alt キャッシュヒット
        Cache-->>Main: cached_result
        Note over Main: 処理時間: <1ms
    else キャッシュミス
        Main->>Preprocessor: preprocess(code)
        Note over Preprocessor: 関数マクロ展開含む<br/>処理時間: 1-50ms
        Preprocessor-->>Main: preprocessed_code
        
        Main->>Parser: parse(preprocessed_code)
        Parser-->>Main: parsed_data
        
        Main->>Cache: cache_result(file_path, function, parsed_data)
    end
```

## 10. まとめ

### 関数マクロ対応による主な変更点

1. **Preprocessorの拡張**
   - `_collect_defines()`: 関数マクロも検出
   - `_expand_function_macros()`: 新規追加（多段階展開）
   - `_expand_single_function_macro()`: 新規追加（単一マクロ展開）
   - `_extract_balanced_parentheses()`: 新規追加（括弧抽出）
   - `_parse_macro_arguments()`: 改善（括弧を考慮）

2. **処理フローの追加**
   - 関数マクロ展開 → 通常マクロ展開の順序
   - 最大10回の反復展開（ネスト対応）
   - 循環参照の検出と警告

3. **データ構造の拡張**
   - ParsedDataに`macros_info`フィールド追加
   - Preprocessor内部に`function_macros`辞書追加

4. **エラーハンドリングの強化**
   - 引数数不一致の検出
   - 括弧の不均衡の検出
   - 循環参照の検出

### パフォーマンス特性

- 単純なマクロ: < 1ms
- ネストしたマクロ（3段階）: < 10ms
- 複雑なマクロ（10段階）: < 50ms
- キャッシュヒット時: < 1ms

これにより、実用的なC言語プロジェクトで関数マクロを多用していても、高速な処理が可能です。
