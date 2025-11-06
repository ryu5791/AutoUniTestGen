# C言語単体テスト自動生成ツール - 実装計画

## フェーズ1: 基礎インフラ構築（Phase 1）

### 1.1 データ構造の定義
- [ ] ParsedData クラス
- [ ] TruthTableData クラス
- [ ] TestCode クラス
- [ ] IOTableData クラス

**成果物**: `data_structures.py`

### 1.2 基本的なユーティリティ
- [ ] ファイル読み書き
- [ ] エラーハンドリング
- [ ] ロギング設定

**成果物**: `utils.py`

### 1.3 テスト環境の構築
- [ ] pytestのセットアップ
- [ ] サンプルCコードの準備
- [ ] 期待値データの準備

**成果物**: `tests/` ディレクトリ

---

## フェーズ2: C言語解析機能（Phase 2）

### 2.1 Preprocessor実装
- [ ] コメント削除機能
- [ ] #define展開機能（基本）
- [ ] 不要な#include削除

**成果物**: `preprocessor.py`
**テスト**: `tests/test_preprocessor.py`

### 2.2 ASTBuilder実装
- [ ] pycparserのセットアップ
- [ ] fake_libc_includeの設定
- [ ] AST構築エラーハンドリング

**成果物**: `ast_builder.py`
**テスト**: `tests/test_ast_builder.py`

### 2.3 ConditionExtractor実装
- [ ] if文の抽出
- [ ] switch文の抽出
- [ ] 二項演算子の分解（OR/AND）
- [ ] 条件式の文字列化

**成果物**: `condition_extractor.py`
**テスト**: `tests/test_condition_extractor.py`

### 2.4 CCodeParser統合
- [ ] 各コンポーネントの統合
- [ ] エンドツーエンドテスト

**成果物**: `c_code_parser.py`
**テスト**: `tests/test_c_code_parser.py`

**マイルストーン**: f1_target.cを解析してParseDataを生成できる

---

## フェーズ3: 真偽表生成機能（Phase 3）

### 3.1 ConditionAnalyzer実装
- [ ] 単純条件の判定
- [ ] OR条件の判定と分解
- [ ] AND条件の判定と分解
- [ ] switch文の分析

**成果物**: `condition_analyzer.py`
**テスト**: `tests/test_condition_analyzer.py`

### 3.2 MCDCPatternGenerator実装
- [ ] OR条件のMC/DCパターン生成（TF, FT, FF）
- [ ] AND条件のMC/DCパターン生成（TF, FT, TT）
- [ ] 複雑な条件の組み合わせ

**成果物**: `mcdc_pattern_generator.py`
**テスト**: `tests/test_mcdc_pattern_generator.py`

### 3.3 TruthTableGenerator統合
- [ ] テストケース番号の採番
- [ ] 期待値の自動生成（基本）
- [ ] テーブルデータの構築

**成果物**: `truth_table_generator.py`
**テスト**: `tests/test_truth_table_generator.py`

### 3.4 ExcelWriter実装（真偽表）
- [ ] openpyxlのセットアップ
- [ ] ヘッダー行の作成
- [ ] データ行の書き込み
- [ ] セルフォーマット（罫線、色）

**成果物**: `excel_writer.py`
**テスト**: `tests/test_excel_writer.py`

**マイルストーン**: f1_target.cから真偽表Excelを生成できる

---

## フェーズ4: Unityテストコード生成（Phase 4）

### 4.1 MockGenerator実装
- [ ] 外部関数のリスト化
- [ ] モック変数の生成（戻り値、呼び出し回数）
- [ ] モック関数の実装生成
- [ ] リセット関数の生成

**成果物**: `mock_generator.py`
**テスト**: `tests/test_mock_generator.py`

### 4.2 BoundaryValueCalculator実装
- [ ] 比較演算子の解析（>, <, >=, <=, ==, !=）
- [ ] 境界値の計算
  - `v10 > 30` → T: 31, F: 30
  - `v10 < -30` → T: -31, F: -30

**成果物**: `boundary_value_calculator.py`
**テスト**: `tests/test_boundary_value_calculator.py`

### 4.3 CommentGenerator実装
- [ ] 対象分岐のコメント生成
- [ ] 条件のコメント生成（真偽値付き）
- [ ] 期待動作のコメント生成

**成果物**: `comment_generator.py`
**テスト**: `tests/test_comment_generator.py`

### 4.4 TestFunctionGenerator実装
- [ ] テスト名の生成（ルール準拠）
- [ ] 変数初期化コードの生成
- [ ] モック設定コードの生成
- [ ] 対象関数呼び出しコードの生成
- [ ] TEST_ASSERT_EQUAL の生成
- [ ] 呼び出し回数チェックの生成

**成果物**: `test_function_generator.py`
**テスト**: `tests/test_test_function_generator.py`

### 4.5 PrototypeGenerator実装
- [ ] static宣言の追加
- [ ] モック関数のプロトタイプ
- [ ] テスト関数のプロトタイプ
- [ ] 適切な順序での配置

**成果物**: `prototype_generator.py`
**テスト**: `tests/test_prototype_generator.py`

### 4.6 UnityTestGenerator統合
- [ ] ヘッダーの生成（#include等）
- [ ] 型定義の生成
- [ ] setUp/tearDownの生成
- [ ] 全コンポーネントの統合

**成果物**: `unity_test_generator.py`
**テスト**: `tests/test_unity_test_generator.py`

**マイルストーン**: f1_target.cからUnityテストコード(.c)を生成できる

---

## フェーズ5: I/O表生成機能（Phase 5）

### 5.1 VariableExtractor実装
- [ ] テスト関数から入力変数を抽出
- [ ] テスト関数から出力変数を抽出
- [ ] 変数の値を抽出

**成果物**: `variable_extractor.py`
**テスト**: `tests/test_variable_extractor.py`

### 5.2 IOTableGenerator実装
- [ ] 全テストケースの入出力変数を収集
- [ ] テーブルデータの構築
- [ ] "-" の自動挿入（ケアしていない変数）

**成果物**: `io_table_generator.py`
**テスト**: `tests/test_io_table_generator.py`

### 5.3 ExcelWriter拡張（I/O表）
- [ ] I/O表形式のExcel生成
- [ ] ヘッダーの2行構造（input/output）
- [ ] データ行の書き込み

**成果物**: `excel_writer.py`（拡張）
**テスト**: `tests/test_excel_writer.py`（追加）

**マイルストーン**: 生成されたテストコードからI/O表Excelを生成できる

---

## フェーズ6: 統合とメインプログラム（Phase 6）

### 6.1 CTestAutoGenerator実装
- [ ] 全コンポーネントの統合
- [ ] エラーハンドリングの実装
- [ ] 進捗表示の実装

**成果物**: `c_test_auto_generator.py`
**テスト**: `tests/test_integration.py`

### 6.2 CLIインターフェース
- [ ] argparseでのコマンドライン引数処理
- [ ] 使い方のヘルプ表示
- [ ] オプション設定（出力先等）

**成果物**: `main.py` または `cli.py`

### 6.3 設定ファイル対応
- [ ] YAML/JSON設定ファイルの読み込み
- [ ] カスタムテンプレートの対応
- [ ] 命名規則のカスタマイズ

**成果物**: `config.py`, `config.yaml`

**マイルストーン**: コマンド一つで全ファイル生成が完了

---

## フェーズ7: 改善と最適化（Phase 7）

### 7.1 エラーハンドリングの強化
- [ ] より詳細なエラーメッセージ
- [ ] 部分的な失敗への対応
- [ ] リトライ機構

### 7.2 パフォーマンス最適化
- [ ] 大規模ファイルへの対応
- [ ] キャッシュ機構の導入
- [ ] 並列処理の検討

### 7.3 ドキュメント整備
- [ ] README.md
- [ ] API ドキュメント
- [ ] チュートリアル
- [ ] トラブルシューティングガイド

---

## 依存ライブラリ

```python
# requirements.txt
pycparser==2.21          # C言語パーサ
openpyxl==3.1.2          # Excel読み書き
pytest==7.4.0            # テストフレームワーク
pytest-cov==4.1.0        # カバレッジ測定
pyyaml==6.0              # 設定ファイル
click==8.1.0             # CLIフレームワーク（optional）
```

---

## ディレクトリ構造

```
c_test_auto_generator/
├── README.md
├── requirements.txt
├── setup.py
├── config.yaml
├── design_sequence_diagram.md
├── design_class_diagram.md
├── design_implementation_plan.md
├── src/
│   ├── __init__.py
│   ├── main.py
│   ├── c_test_auto_generator.py
│   ├── data_structures.py
│   ├── utils.py
│   ├── parser/
│   │   ├── __init__.py
│   │   ├── c_code_parser.py
│   │   ├── preprocessor.py
│   │   ├── ast_builder.py
│   │   └── condition_extractor.py
│   ├── truth_table/
│   │   ├── __init__.py
│   │   ├── truth_table_generator.py
│   │   ├── condition_analyzer.py
│   │   └── mcdc_pattern_generator.py
│   ├── test_generator/
│   │   ├── __init__.py
│   │   ├── unity_test_generator.py
│   │   ├── mock_generator.py
│   │   ├── test_function_generator.py
│   │   ├── comment_generator.py
│   │   ├── prototype_generator.py
│   │   └── boundary_value_calculator.py
│   ├── io_table/
│   │   ├── __init__.py
│   │   ├── io_table_generator.py
│   │   └── variable_extractor.py
│   └── output/
│       ├── __init__.py
│       └── excel_writer.py
├── tests/
│   ├── __init__.py
│   ├── fixtures/
│   │   ├── sample1.c
│   │   └── expected_output/
│   ├── test_preprocessor.py
│   ├── test_ast_builder.py
│   ├── test_condition_extractor.py
│   └── ... (その他のテストファイル)
└── examples/
    ├── f1_target.c
    └── generated/
        ├── truth_table.xlsx
        ├── test_generated.c
        └── io_table.xlsx
```

---

## 開発の進め方

1. **Phase 1-2**: まず基礎とC言語解析機能を実装
2. **Phase 3**: 真偽表生成機能を実装
3. **Phase 4**: Unityテストコード生成を実装
4. **Phase 5**: I/O表生成機能を実装
5. **Phase 6**: 統合とCLI実装
6. **Phase 7**: 改善と最適化

各フェーズ終了時にマイルストーンを達成し、動作確認を行う。
