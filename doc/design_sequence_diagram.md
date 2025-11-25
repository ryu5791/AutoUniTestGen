# C言語単体テスト自動生成ツール - シーケンス図 (v2.10.1)

## 1. 全体処理フロー

```mermaid
sequenceDiagram
    actor User
    participant Config as config.ini
    participant EncConfig as EncodingConfig
    participant Main as メインプログラム
    participant Parser as CCodeParser
    participant TruthTable as TruthTableGenerator
    participant TestGen as UnityTestGenerator
    participant IOTable as IOTableGenerator
    participant Excel as ExcelWriter

    User->>Config: 設定ファイル編集(output_encoding)
    User->>Main: C言語ファイルを指定
    
    Note over Main: 初期化フェーズ
    Main->>EncConfig: load_encoding_config()
    EncConfig->>Config: read config.ini
    Config-->>EncConfig: output_encoding = "shift_jis"
    EncConfig-->>Main: エンコーディング設定完了
    
    Main->>Parser: parse(c_file_path)
    
    Note over Parser: C言語ファイルを解析
    Parser->>Parser: プリプロセス処理
    Parser->>Parser: AST生成
    Parser->>Parser: 関数抽出
    Parser->>Parser: 条件分岐抽出
    Parser->>Parser: 構造体定義抽出(2パス処理)
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
    TestGen->>TestGen: ネスト構造体展開
    TestGen->>TestGen: プロトタイプ宣言生成
    TestGen->>TestGen: コメント生成
    TestGen-->>Main: TestCode
    
    Main->>EncConfig: get_output_encoding()
    EncConfig-->>Main: "shift_jis"
    Main->>TestGen: save(output_path, encoding="shift_jis")
    TestGen-->>Main: test_generated.c (Shift-JIS)
    
    Main->>IOTable: generate(test_code, truth_table)
    Note over IOTable: I/O一覧表を生成
    IOTable->>IOTable: 入力変数抽出
    IOTable->>IOTable: 出力変数抽出
    IOTable->>IOTable: モック関数検出
    IOTable-->>Main: IOTableData
    
    Main->>Excel: write_io_table(io_data)
    Excel-->>Main: io_table.xlsx
    
    Main-->>User: 生成完了（3ファイル）
```

## 2. エンコーディング処理の詳細フロー (v2.10.1 新規)

```mermaid
sequenceDiagram
    participant Main as メインプログラム
    participant EncConfig as EncodingConfig
    participant Config as config.ini
    participant TestCode as TestCode
    participant FileSystem as ファイルシステム
    
    Note over EncConfig: モジュール読み込み時
    EncConfig->>Config: ConfigParser.read("config.ini")
    Config-->>EncConfig: [output] output_encoding = "shift_jis"
    EncConfig->>EncConfig: OUTPUT_ENCODING = "shift_jis"
    
    Note over Main: テストコード保存時
    Main->>TestCode: save(filepath)
    TestCode->>EncConfig: get_output_encoding()
    EncConfig-->>TestCode: "shift_jis"
    TestCode->>FileSystem: open(filepath, 'w', encoding='shift_jis')
    FileSystem-->>TestCode: ファイルハンドル
    TestCode->>FileSystem: write(content)
    TestCode->>FileSystem: close()
    
    Note over Main: スタンドアロンモード時
    Main->>EncConfig: get_output_encoding()
    EncConfig-->>Main: "shift_jis"
    Main->>FileSystem: open(filepath, 'w', encoding='shift_jis')
    FileSystem-->>Main: ファイルハンドル
    Main->>FileSystem: write(standalone_code)
    Main->>FileSystem: close()
```

## 3. ファイル読み込み処理（自動エンコーディング検出）

```mermaid
sequenceDiagram
    participant Parser as CCodeParser
    participant Utils as utils.read_file()
    participant FileSystem as ファイルシステム
    
    Parser->>Utils: read_file(filepath, encoding='auto')
    
    loop エンコーディング試行
        Utils->>Utils: encodings = [utf-8, cp932, shift-jis, euc-jp, ...]
        Utils->>FileSystem: open(filepath, 'r', encoding=enc)
        
        alt 成功
            FileSystem-->>Utils: ファイル内容
            Utils-->>Parser: 内容（文字列）
        else UnicodeDecodeError
            Utils->>Utils: 次のエンコーディングを試行
        end
    end
    
    alt すべて失敗
        Utils-->>Parser: IOError（エンコーディング検出失敗）
    end
```

## 4. 構造体定義の2パス処理 (v2.9.0で追加)

```mermaid
sequenceDiagram
    participant Parser as TypedefExtractor
    participant AST as AST
    participant StructMap as 構造体マップ
    
    Note over Parser: 第1パス - 構造体定義収集
    loop 各ノード
        Parser->>AST: walk_ast()
        AST-->>Parser: typedef struct ノード
        Parser->>Parser: parse_typedef_struct(resolve_types=False)
        Parser->>StructMap: 構造体定義を追加（型未解決）
    end
    
    Note over Parser: 第2パス - 型参照解決
    loop 各構造体定義
        Parser->>StructMap: get_struct(member.type)
        
        alt 構造体型メンバー
            StructMap-->>Parser: ネストされた構造体定義
            Parser->>Parser: member.nested_struct = struct_def
        else 基本型メンバー
            Parser->>Parser: そのまま保持
        end
    end
    
    Parser-->>Parser: 完全に解決された構造体定義リスト
```

## 5. テスト生成の詳細フロー

```mermaid
sequenceDiagram
    participant Gen as TestFunctionGenerator
    participant Struct as StructDefinition
    participant Code as 生成コード
    
    Gen->>Struct: get_all_members_flat()
    
    Note over Struct: 再帰的展開
    loop 各メンバー
        alt ネスト構造体
            Struct->>Struct: nested_struct.get_all_members_flat()
            Struct->>Struct: パスを結合 (parent.child.field)
        else 通常メンバー
            Struct->>Struct: そのままリストに追加
        end
    end
    
    Struct-->>Gen: フラット化されたメンバーリスト
    
    loop 各フラットメンバー
        Gen->>Code: TEST_ASSERT_EQUAL(expected.path, actual.path)
    end
```

## 6. I/O表生成フロー

```mermaid
sequenceDiagram
    participant IOGen as IOTableGenerator
    participant TestCode as TestCode
    participant Parser as IOVariableExtractor
    participant Excel as ExcelWriter
    
    IOGen->>TestCode: get_test_functions()
    TestCode-->>IOGen: テスト関数リスト
    
    loop 各テスト関数
        IOGen->>Parser: extract_variables(function_code)
        Parser->>Parser: 正規表現で変数抽出
        Parser->>Parser: 入力/出力を分類
        Parser-->>IOGen: 変数情報
        
        IOGen->>IOGen: I/O行データを作成
    end
    
    IOGen->>Excel: create_io_table(io_data)
    Excel->>Excel: ワークシート作成
    Excel->>Excel: ヘッダー設定
    Excel->>Excel: データ行追加
    Excel-->>IOGen: io_table.xlsx
```

## 7. エラーハンドリングフロー

```mermaid
sequenceDiagram
    participant Main as メインプログラム
    participant Component as 各コンポーネント
    participant Logger as ロガー
    participant User as ユーザー
    
    Main->>Component: 処理実行
    
    alt 正常終了
        Component-->>Main: 結果データ
        Main->>Logger: INFO: 処理成功
    else エラー発生
        Component-->>Main: Exception
        Main->>Logger: ERROR: エラー詳細
        
        alt リカバリ可能
            Main->>Component: フォールバック処理
            Component-->>Main: 代替結果
            Main->>Logger: WARNING: フォールバック使用
        else リカバリ不可
            Main->>User: エラーメッセージ表示
            Main->>Main: 処理中断
        end
    end
```

## 更新履歴

- **v2.10.1 (2025-11-21)**: エンコーディング設定処理を追加
- **v2.10.0 (2025-11-21)**: UTF-8対応（削除）
- **v2.9.0 (2025-11-21)**: 構造体の2パス処理を追加
- **v2.8.0**: ネスト構造体展開処理を追加
- **v2.7.0**: 初期バージョン
