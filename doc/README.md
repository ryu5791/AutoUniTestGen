# C言語単体テスト自動生成ツール (Phase 7完了版)

C言語ソースコードから以下を**自動生成**するツール：

1. ✅ **MC/DC真偽表** (Excel形式) - 100%カバレッジ
2. ✅ **Unityテストコード** (C言語) - 実行可能なテストファイル
3. ✅ **I/O一覧表** (Excel形式) - 入出力値の一覧

## 🎯 主な機能

### 基本機能
- **MC/DCカバレッジ**: Modified Condition/Decision Coverage を満たすテストケースを自動生成
- **Unity対応**: Unity Test Framework用のテストコードを生成
- **モック/スタブ**: 外部関数呼び出しのモック/スタブを自動生成
- **境界値分析**: 条件式から境界値を自動計算
- **詳細コメント**: テストケース毎に説明コメントを付与
- **Excel出力**: 真偽表とI/O表を見やすいExcel形式で出力

### Phase 7の新機能 🆕
- **エラーハンドリング強化**: 詳細なエラーメッセージとリカバリーヒント
- **バッチ処理**: 複数ファイルの一括処理、並列実行対応
- **パフォーマンス最適化**: パフォーマンス監視、メモリ管理、結果キャッシュ
- **カスタムテンプレート**: テストコードのテンプレートをカスタマイズ可能
- **拡張CLI**: 20種類以上の新しいコマンドラインオプション

## 📋 必要要件

- Python 3.8以上
- 以下のPythonパッケージ：
  - pycparser (C言語パーサー)
  - openpyxl (Excel操作)
  - psutil (パフォーマンス監視)

## 🔧 インストール

### 1. リポジトリをクローン

```bash
git clone https://github.com/your-repo/AutoUniTestGen.git
cd AutoUniTestGen
```

### 2. 依存パッケージをインストール

```bash
pip install pycparser openpyxl psutil
```

または

```bash
pip install -r requirements.txt
```

## 🚀 使い方

### 基本的な使い方

C言語ファイルと対象関数を指定して実行：

```bash
python main.py -i sample.c -f calculate -o output
```

これで以下のファイルが`output`ディレクトリに生成されます：
- `sample_calculate_truth_table.xlsx` (真偽表)
- `test_sample_calculate.c` (テストコード)
- `sample_calculate_io_table.xlsx` (I/O表)

### コマンドラインオプション

```bash
# すべて生成（デフォルト）
python main.py -i file.c -f func_name -o output

# 真偽表のみ生成
python main.py -i file.c -f func_name -o output --truth-only

# テストコードのみ生成
python main.py -i file.c -f func_name -o output --test-only

# I/O表のみ生成
python main.py -i file.c -f func_name -o output --io-only

# カスタムファイル名を指定
python main.py -i file.c -f func_name -o output \
  --truth-table my_truth.xlsx \
  --test-code my_test.c \
  --io-table my_io.xlsx

# 設定ファイルを使用
python main.py -i file.c -f func_name -c config.json

# ヘルプを表示
python main.py --help

# バージョン表示
python main.py --version
```

### Phase 7の新機能の使い方 🆕

#### バッチ処理

```bash
# バッチ設定ファイルを作成
python main.py --create-batch-config batch_config.json

# バッチ処理を実行
python main.py --batch batch_config.json

# 並列処理（4ワーカー）
python main.py --batch batch_config.json --parallel --workers 4

# ディレクトリ一括処理
python main.py --batch-dir src/ --pattern "*.c"

# 結果をJSON保存
python main.py --batch batch_config.json --save-results results.json

# エラーが発生しても継続
python main.py --batch batch_config.json --continue-on-error
```

**バッチ設定ファイルの例** (`batch_config.json`):
```json
{
  "items": [
    {
      "input_file": "sample1.c",
      "function_name": "function1",
      "output_dir": "output/sample1"
    },
    {
      "input_file": "sample2.c",
      "function_name": "function2",
      "output_dir": "output/sample2"
    }
  ]
}
```

#### パフォーマンス監視

```bash
# パフォーマンス監視を有効化
python main.py -i sample.c -f calculate --performance

# メモリ制限を設定（MB単位）
python main.py -i sample.c -f calculate --memory-limit 500

# キャッシュを無効化
python main.py -i sample.c -f calculate --no-cache
```

#### ログ制御

```bash
# ログレベルを設定
python main.py -i sample.c -f calculate --log-level DEBUG

# ログをファイルに出力
python main.py -i sample.c -f calculate --log-file output.log

# 詳細な出力
python main.py -i sample.c -f calculate --verbose
```

#### カスタムテンプレート

```bash
# サンプルテンプレートファイルを作成
python main.py --create-templates templates/

# 利用可能なテンプレートを表示
python main.py --list-templates

# カスタムテンプレートを使用
python main.py -i sample.c -f calculate --template my_template
```

### Pythonスクリプトから使用

```python
from src.c_test_auto_generator import CTestAutoGenerator

# 生成器を初期化
generator = CTestAutoGenerator()

# すべての成果物を一括生成
result = generator.generate_all(
    c_file_path="sample.c",
    target_function="calculate",
    output_dir="output"
)

# 結果を表示
print(result)

# 真偽表のみ生成
result = generator.generate_truth_table_only(
    c_file_path="sample.c",
    target_function="calculate",
    output_path="output/truth_table.xlsx"
)
```

## 📁 プロジェクト構造

```
AutoUniTestGen/
├── main.py                      # エントリーポイント
├── README.md                    # このファイル
├── requirements.txt             # 依存パッケージ
├── src/
│   ├── __init__.py
│   ├── data_structures.py       # データクラス定義
│   ├── utils.py                 # ユーティリティ関数
│   ├── config.py                # 設定管理
│   ├── cli.py                   # CLIインターフェース (Phase 7拡張)
│   ├── c_test_auto_generator.py # 統合クラス
│   ├── error_handler.py         # エラーハンドリング (Phase 7)
│   ├── batch_processor.py       # バッチ処理 (Phase 7)
│   ├── performance.py           # パフォーマンス最適化 (Phase 7)
│   ├── template_engine.py       # テンプレートエンジン (Phase 7)
│   ├── parser/                  # C言語解析
│   │   ├── preprocessor.py
│   │   ├── ast_builder.py
│   │   ├── condition_extractor.py
│   │   └── c_code_parser.py
│   ├── truth_table/             # 真偽表生成
│   │   ├── condition_analyzer.py
│   │   ├── mcdc_pattern_generator.py
│   │   └── truth_table_generator.py
│   ├── test_generator/          # テストコード生成
│   │   ├── boundary_value_calculator.py
│   │   ├── mock_generator.py
│   │   ├── comment_generator.py
│   │   ├── test_function_generator.py
│   │   ├── prototype_generator.py
│   │   └── unity_test_generator.py
│   ├── io_table/                # I/O表生成
│   │   ├── variable_extractor.py
│   │   └── io_table_generator.py
│   └── output/                  # Excel出力
│       └── excel_writer.py
├── doc/                         # ドキュメント
│   ├── PHASE1-2_COMPLETION_REPORT.md
│   ├── PHASE3_COMPLETION_REPORT.md
│   ├── PHASE4_COMPLETION_REPORT.md
│   ├── PHASE4_BUGFIX_REPORT.md
│   ├── PHASE5_IMPACT_ANALYSIS.md
│   └── PHASE6_COMPLETION_REPORT.md
└── test_*.py                    # 統合テスト
```

## 🔍 使用例

### 入力：C言語ソースコード

```c
int calculate(int a, int b, int c) {
    if (a > 10) {
        if (b < 20) {
            return c * 2;
        } else {
            return c + 10;
        }
    } else {
        return c - 5;
    }
}
```

### 出力1：真偽表 (Excel)

| No | テストケース | a > 10 | b < 20 | 期待値 |
|----|-------------|--------|--------|--------|
| 1  | TC_1        | T      | T      | c * 2  |
| 2  | TC_2        | T      | F      | c + 10 |
| 3  | TC_3        | F      | -      | c - 5  |

### 出力2：テストコード (C言語)

```c
#include "unity.h"
#include "calculate.h"

void test_calculate_TC_1(void) {
    // a > 10: TRUE, b < 20: TRUE
    // 期待値: c * 2
    int a = 11;
    int b = 19;
    int c = 5;
    int expected = 10;
    
    int actual = calculate(a, b, c);
    TEST_ASSERT_EQUAL_INT(expected, actual);
}

// ... その他のテスト関数
```

### 出力3：I/O表 (Excel)

|    |         | input | input | input | output |
|----|---------|-------|-------|-------|--------|
| No | テスト名 | a     | b     | c     | 戻り値  |
| 1  | TC_1    | 11    | 19    | 5     | 10     |
| 2  | TC_2    | 11    | 21    | 5     | 15     |
| 3  | TC_3    | 9     | -     | 5     | 0      |

## ⚙️ 設定ファイル

デフォルト設定ファイルを作成：

```bash
python main.py --create-config generator_config.json
```

設定ファイルの例：

```json
{
  "output_dir": "output",
  "truth_table_suffix": "_truth_table.xlsx",
  "test_code_prefix": "test_",
  "io_table_suffix": "_io_table.xlsx",
  "include_paths": [],
  "define_macros": {},
  "test_framework": "Unity",
  "include_mock_stubs": true,
  "include_comments": true,
  "excel_format": "xlsx",
  "include_header_color": true
}
```

## 🧪 テスト

統合テストを実行：

```bash
# Phase 6統合テスト
python test_phase6_integration.py

# Phase 5統合テスト
python doc/test_phase5_integration.py

# Phase 4統合テスト
python doc/test_phase4_integration.py
```

## 📚 ドキュメント

詳細なドキュメントは`doc/`ディレクトリを参照：

- `design_implementation_plan.md` - 実装計画
- `design_class_diagram.md` - クラス図
- `design_sequence_diagram.md` - シーケンス図
- `PHASE*_COMPLETION_REPORT.md` - 各フェーズの完了レポート

## 🐛 既知の制限事項

- 現在サポートしているのは単純なif文とswitch文のみ
- ネストが深い条件分岐は複雑になる場合があります
- マクロが多用されているコードは前処理が必要

## 🔄 開発状況

- [x] Phase 1: 基礎インフラ (100%)
- [x] Phase 2: C言語解析 (100%)
- [x] Phase 3: 真偽表生成 (100%)
- [x] Phase 4: テストコード生成 (100%)
- [x] Phase 5: I/O表生成 (100%)
- [x] Phase 6: 統合とCLI (100%)
- [ ] Phase 7: 改善と最適化 (予定)

**現在の進捗: 86% (6/7フェーズ完了)**

## 📝 ライセンス

MIT License

## 👥 貢献

プルリクエストを歓迎します！

## 📧 お問い合わせ

問題や質問がある場合は、Issueを作成してください。

---

**バージョン**: 1.0.0  
**最終更新**: 2025-11-07
