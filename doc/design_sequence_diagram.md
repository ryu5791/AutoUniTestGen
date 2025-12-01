# AutoUniTestGen v4.1 - シーケンス図

## 概要
C言語単体テスト自動生成ツール AutoUniTestGen v4.1のシーケンス図

### v4.0からの主な変更点
- **標準ライブラリ関数除外処理**: `#include`解析による自動除外
- **シグネチャ一致モック生成**: 元の関数と同じシグネチャでモック生成
- **エンコーディング自動検出**: UTF-8/Shift-JIS自動判別、Shift-JIS出力

---

## 1. 全体処理フロー

```mermaid
sequenceDiagram
    actor User
    participant Main as CTestAutoGenerator
    participant Encoding as EncodingUtils
    participant Parser as CCodeParser
    participant TruthTable as TruthTableGenerator
    participant TestGen as UnityTestGenerator
    participant IOTable as IOTableGenerator
    participant Excel as ExcelWriter

    User->>Main: generate_all(c_file_path, target_function, output_dir)
    
    Note over Main: Step 1: C言語ファイル解析
    Main->>Parser: parse(c_file_path, target_function)
    Parser-->>Main: ParsedData（関数情報, 条件分岐, シグネチャ）
    
    Note over Main: Step 2: ソースコード読み込み（エンコーディング自動検出）
    Main->>Encoding: read_source_file(c_file_path)
    Encoding-->>Main: (source_code, detected_encoding)
    
    Note over Main: Step 3: MC/DC真偽表生成
    Main->>TruthTable: generate(parsed_data)
    TruthTable-->>Main: TruthTableData
    
    Main->>Excel: write_truth_table(truth_table, filepath)
    Excel-->>Main: truth_table.xlsx
    
    Note over Main: Step 4: Unityテストコード生成
    Main->>TestGen: generate_standalone(truth_table, parsed_data, source_code)
    TestGen-->>Main: standalone_code
    
    Main->>Encoding: write_source_file(filepath, code, 'shift_jis')
    Encoding-->>Main: success
    
    Note over Main: Step 5: I/O表生成
    Main->>IOTable: generate(test_code, truth_table)
    IOTable-->>Main: IOTableData
    
    Main->>Excel: write_io_table(io_table, filepath)
    Excel-->>Main: io_table.xlsx
    
    Main-->>User: GenerationResult（3ファイル生成完了）
```

---

## 2. CCodeParser詳細シーケンス（v4.1更新）

```mermaid
sequenceDiagram
    participant Main as CTestAutoGenerator
    participant Parser as CCodeParser
    participant Preprocessor as Preprocessor
    participant ASTBuilder as ASTBuilder
    participant CondExtractor as ConditionExtractor
    participant StdlibExtractor as StdlibFunctionExtractor

    Main->>Parser: parse(c_file_path, target_function)
    
    Note over Parser: 1. ファイル読み込み
    Parser->>Parser: _read_file(c_file_path)
    
    Note over Parser: 2. プリプロセス処理
    Parser->>Preprocessor: preprocess(c_code)
    Preprocessor->>Preprocessor: _remove_comments()
    Preprocessor->>Preprocessor: _process_defines()
    Preprocessor->>Preprocessor: _handle_includes()
    Preprocessor-->>Parser: preprocessed_code
    
    Note over Parser: 3. AST構築
    Parser->>ASTBuilder: build_ast_with_fallback(preprocessed_code)
    
    alt AST構築成功
        ASTBuilder-->>Parser: ast
    else AST構築失敗
        ASTBuilder->>ASTBuilder: フォールバックモード
        ASTBuilder-->>Parser: partial_ast
    end
    
    Note over Parser: 4. 関数情報・シグネチャ抽出
    Parser->>Parser: _extract_function_info(ast, target_function)
    Parser->>Parser: _extract_function_signatures(ast, code)
    
    Note over Parser: 5. 条件分岐抽出
    Parser->>CondExtractor: extract_conditions(ast)
    CondExtractor->>CondExtractor: visit_FuncDef()
    CondExtractor->>CondExtractor: visit_If()
    CondExtractor->>CondExtractor: visit_Switch()
    CondExtractor-->>Parser: conditions_list
    
    Note over Parser: 6. 外部関数抽出（v4.1: 標準ライブラリ除外）
    Parser->>Parser: _extract_external_functions(conditions, ast, source_code)
    Parser->>StdlibExtractor: filter_external_functions(functions, source_code)
    
    Note over StdlibExtractor: #includeを解析して標準ライブラリ関数を除外
    StdlibExtractor->>StdlibExtractor: extract_includes_from_source()
    StdlibExtractor->>StdlibExtractor: is_stdlib_function() for each
    StdlibExtractor-->>Parser: filtered_external_functions
    
    Note over Parser: 7. グローバル変数・enum抽出
    Parser->>Parser: _extract_global_variables(ast)
    Parser->>Parser: _extract_enums(ast)
    
    Parser-->>Main: ParsedData
```

---

## 3. 標準ライブラリ関数除外処理（v4.1新規）

```mermaid
sequenceDiagram
    participant Parser as CCodeParser
    participant StdlibExtractor as StdlibFunctionExtractor
    participant FileSystem as ファイルシステム

    Parser->>StdlibExtractor: filter_external_functions(external_funcs, source_code)
    
    Note over StdlibExtractor: 1. #includeディレクティブを抽出
    StdlibExtractor->>StdlibExtractor: extract_includes_from_source(source_code)
    Note right of StdlibExtractor: #include <stdio.h><br/>#include <stdlib.h><br/>#include <math.h><br/>#include "my_header.h"
    
    loop 各インクルードヘッダ
        alt 標準ライブラリヘッダ
            StdlibExtractor->>StdlibExtractor: is_stdlib_header(header)?
            
            Note over StdlibExtractor: 2. ヘッダファイルを検索
            StdlibExtractor->>FileSystem: find_header_file(header_name)
            
            alt ヘッダファイル発見
                FileSystem-->>StdlibExtractor: /usr/include/stdio.h
                
                Note over StdlibExtractor: 3. ヘッダから関数宣言を抽出
                StdlibExtractor->>StdlibExtractor: extract_functions_from_header()
                Note right of StdlibExtractor: printf, scanf, fopen...<br/>正規表現で関数宣言を解析
                
            else ヘッダファイル未発見
                Note over StdlibExtractor: フォールバックリスト使用
                StdlibExtractor->>StdlibExtractor: use FALLBACK_STDLIB_FUNCTIONS
            end
        else ユーザーヘッダ
            Note over StdlibExtractor: スキップ（モック対象）
        end
    end
    
    Note over StdlibExtractor: 4. 外部関数をフィルタリング
    loop 各外部関数
        StdlibExtractor->>StdlibExtractor: is_stdlib_function(func_name)?
        
        alt 標準ライブラリ関数
            Note right of StdlibExtractor: abs, printf, strlen → 除外
        else ユーザー定義関数
            Note right of StdlibExtractor: Utf8, my_func → 残す
        end
    end
    
    StdlibExtractor-->>Parser: filtered_functions（標準ライブラリ除外済み）
```

---

## 4. モック生成処理（v4.0/v4.1更新）

```mermaid
sequenceDiagram
    participant TestGen as UnityTestGenerator
    participant MockGen as MockGenerator
    participant ParsedData as ParsedData

    TestGen->>MockGen: generate_mocks(parsed_data)
    
    Note over MockGen: 1. 外部関数リストを取得（標準ライブラリ除外済み）
    MockGen->>ParsedData: external_functions
    ParsedData-->>MockGen: ['Utf8', 'Utf9', 'f4', 'mx27']
    
    Note over MockGen: 2. シグネチャ情報を取得
    MockGen->>ParsedData: function_signatures
    ParsedData-->>MockGen: {Utf8: FunctionSignature, ...}
    
    loop 各外部関数
        MockGen->>MockGen: _create_mock_function(func_name, signature)
        
        alt シグネチャあり
            Note right of MockGen: uint8_t Utf8(void)<br/>uint16_t Utf9(uint8_t, int)
            MockGen->>MockGen: 元のシグネチャを使用
        else シグネチャなし
            MockGen->>MockGen: _guess_return_type()でフォールバック
        end
    end
    
    Note over MockGen: 3. モック変数生成
    MockGen->>MockGen: generate_mock_variables()
    Note right of MockGen: static uint8_t mock_Utf8_return_value;<br/>static int mock_Utf8_call_count;<br/>static uint8_t mock_Utf9_param_param1;
    
    Note over MockGen: 4. モック関数生成（元の関数と同名・同シグネチャ）
    MockGen->>MockGen: generate_mock_functions()
    Note right of MockGen: uint8_t Utf8(void) {<br/>  mock_Utf8_call_count++;<br/>  return mock_Utf8_return_value;<br/>}
    
    Note over MockGen: 5. void型関数の特別処理
    Note right of MockGen: void Utf10(uint8_t Utv2) {<br/>  mock_Utf10_call_count++;<br/>  mock_Utf10_param_Utv2 = Utv2;<br/>  // return文なし<br/>}
    
    Note over MockGen: 6. リセット関数生成
    MockGen->>MockGen: generate_reset_function()
    
    MockGen-->>TestGen: mock_code
```

---

## 5. TruthTableGenerator詳細シーケンス

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
            CondAnalyzer->>CondAnalyzer: 条件式解析
            CondAnalyzer-->>TruthGen: {type: "simple", patterns: ["T", "F"]}
            
        else OR条件 (A || B)
            CondAnalyzer->>CondAnalyzer: _build_condition_tree()
            CondAnalyzer->>MCDCGen: generate_patterns(tree)
            MCDCGen->>MCDCGen: _generate_independence_pairs()
            MCDCGen-->>CondAnalyzer: ["TF", "FT", "FF"]
            CondAnalyzer-->>TruthGen: {type: "or", patterns: [...]}
            
        else AND条件 (A && B)
            CondAnalyzer->>CondAnalyzer: _build_condition_tree()
            CondAnalyzer->>MCDCGen: generate_patterns(tree)
            MCDCGen-->>CondAnalyzer: ["TF", "FT", "TT"]
            CondAnalyzer-->>TruthGen: {type: "and", patterns: [...]}
            
        else 複合条件 (A || B || (C && D))
            CondAnalyzer->>CondAnalyzer: _build_condition_tree()
            Note right of CondAnalyzer: ツリー構造で解析
            CondAnalyzer->>MCDCGen: generate_patterns(complex_tree)
            MCDCGen->>MCDCGen: 再帰的にパターン生成
            MCDCGen-->>CondAnalyzer: [6パターン]
            CondAnalyzer-->>TruthGen: {type: "complex", patterns: [...]}
            
        else switch文
            CondAnalyzer->>CondAnalyzer: case文を全抽出
            CondAnalyzer-->>TruthGen: {type: "switch", cases: [0,1,2,...,default]}
        end
    end
    
    TruthGen->>TruthGen: 真偽表データ構築
    TruthGen->>TruthGen: テスト番号採番
    TruthGen-->>Main: TruthTableData
```

---

## 6. エンコーディング処理（v4.0.1新規）

```mermaid
sequenceDiagram
    participant Main as CTestAutoGenerator
    participant Encoding as EncodingUtils
    participant FileSystem as ファイルシステム

    Note over Main,FileSystem: ===== 読み込み処理 =====
    Main->>Encoding: read_source_file(c_file_path)
    
    Encoding->>FileSystem: open(path, encoding='utf-8')
    
    alt UTF-8で成功
        FileSystem-->>Encoding: content
        Encoding-->>Main: (content, 'utf-8')
    else UnicodeDecodeError
        Encoding->>FileSystem: open(path, encoding='shift_jis')
        
        alt Shift-JISで成功
            FileSystem-->>Encoding: content
            Encoding-->>Main: (content, 'shift_jis')
        else 両方失敗
            Encoding-->>Main: (None, 'unknown')
        end
    end
    
    Note over Main,FileSystem: ===== 書き込み処理 =====
    Main->>Encoding: write_source_file(path, content, 'shift_jis')
    
    Encoding->>FileSystem: open(path, 'w', encoding='shift_jis')
    FileSystem-->>Encoding: success
    Encoding-->>Main: True
    
    Note right of Main: 出力は常にShift-JIS<br/>（組込み開発環境互換）
```

---

## 7. スタンドアロンモード処理フロー

```mermaid
sequenceDiagram
    participant Main as CTestAutoGenerator
    participant TestGen as UnityTestGenerator
    participant MockGen as MockGenerator
    participant Encoding as EncodingUtils

    Main->>TestGen: generate_standalone(truth_table, parsed_data, source_code)
    
    Note over TestGen: 1. 元のソースコード全体を基盤として使用
    TestGen->>TestGen: source_code をベースに
    
    Note over TestGen: 2. テスト対象関数本体を抽出
    TestGen->>TestGen: _extract_target_function_body()
    
    Note over TestGen: 3. モック/スタブコードを生成
    TestGen->>MockGen: generate_mocks(parsed_data)
    MockGen-->>TestGen: mock_code
    
    Note over TestGen: 4. テスト関数を生成
    TestGen->>TestGen: _generate_test_functions()
    
    Note over TestGen: 5. Unity関連コードを生成
    TestGen->>TestGen: _generate_unity_includes()
    TestGen->>TestGen: _generate_setup_teardown()
    TestGen->>TestGen: _generate_main()
    
    Note over TestGen: 6. 全コードを結合
    TestGen->>TestGen: ソースコード + モック + テスト関数 + main
    
    TestGen-->>Main: standalone_code
    
    Note over Main: 7. Shift-JISで出力
    Main->>Encoding: write_source_file(path, standalone_code, 'shift_jis')
```

---

## データ構造

### ParsedData（v4.1）
```python
{
    'file_name': '22_難読化_obfuscated.c',
    'function_name': 'Utf1',
    'conditions': [
        {
            'line': 10,
            'type': 'if',
            'expression': '(Utf7() & 0xdf) != 0',
            'ast_node': <AST Node>
        },
        ...
    ],
    'external_functions': ['Utf7', 'Utf8', 'Utf9', ...],  # 標準ライブラリ除外済み
    'global_variables': ['Utv1', 'Utv2', ...],
    'function_signatures': {
        'Utf7': FunctionSignature(name='Utf7', return_type='uint8_t', parameters=[]),
        'Utf8': FunctionSignature(name='Utf8', return_type='void', parameters=[]),
        'Utf9': FunctionSignature(name='Utf9', return_type='uint16_t', 
                                  parameters=[{'type': 'uint8_t', 'name': 'param1'}]),
        ...
    },
    'function_info': FunctionInfo(name='Utf1', return_type='void', ...),
    'bitfields': {...},
    'enums': [...],
    'enum_values': {...}
}
```

### FunctionSignature（v4.0新規）
```python
FunctionSignature(
    name='Utf9',
    return_type='uint16_t',
    parameters=[
        {'type': 'uint8_t', 'name': 'param1'},
        {'type': 'int', 'name': 'param2'}
    ],
    is_static=False
)
```

### MockFunction（v4.0新規）
```python
MockFunction(
    name='Utf9',
    return_type='uint16_t',
    parameters=[
        {'type': 'uint8_t', 'name': 'param1'},
        {'type': 'int', 'name': 'param2'}
    ],
    return_variable='mock_Utf9_return_value',
    call_count_variable='mock_Utf9_call_count'
)
```

---
**バージョン**: 4.1.0  
**更新日**: 2025-12-01
