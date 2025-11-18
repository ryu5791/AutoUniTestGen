# MC/DC テスト実装ドキュメント

## 概要

このドキュメントは、`state_fullopen_func()` 関数内の複雑な条件式に対するMC/DC (Modified Condition/Decision Coverage) 100%カバレッジを達成するテスト実装の詳細を説明します。

## ドキュメント一覧

### 1. [シーケンス図](./MCDC_SEQUENCE_DIAGRAM.md)
テスト実行フローと条件評価のシーケンスを詳細に示した図です。

**含まれる内容:**
- テスト実行フロー全体
- 個別テストケースの実行シーケンス
- MC/DCカバレッジ達成までのプロセス
- カバレッジ検証とレポート生成フロー

### 2. [クラス図](./MCDC_CLASS_DIAGRAM.md)
テスト実装のクラス構造と関係性を示した図です。

**含まれる内容:**
- 全体構造（Unity、TestSuite、GlobalState等）
- テストケースクラス階層（9つのテストケース）
- 条件評価構造（8つの原子条件）
- MC/DCカバレッジ分析構造
- データフロー構造

### 3. [カバレッジレポート](../test/MCDC_COVERAGE_REPORT.md)
MC/DC 100%カバレッジの真偽表と達成状況の詳細レポートです。

**含まれる内容:**
- 対象条件式の詳細
- 8つの原子条件の定義
- 9つのテストケースの真偽表
- 各条件の独立性証明

## 対象条件式

```c
if ((mState.bit.act == ACT_INIT) &&
    ((vHANDY_SET_POWERPON_SEQ == 1) || (vHANDY_SET_POWERPON_SEQ == 2) || (vHANDY_SET_POWERPON_SEQ == 3) ||
     (vHANDY_SET_POWERPON_SEQ == 6) || (vHANDY_SET_POWERPON_SEQ == 7) || (vHANDY_SET_POWERPON_SEQ == 8)) &&
    (vHANDY_SET_OP_POWER_PUSH == 0))
```

## 8つの原子条件

| ID | 条件式 | 説明 |
|----|--------|------|
| C1 | `mState.bit.act == ACT_INIT` | 状態がACT_INITである |
| C2 | `vHANDY_SET_POWERPON_SEQ == 1` | パワーオンシーケンス = 1 |
| C3 | `vHANDY_SET_POWERPON_SEQ == 2` | パワーオンシーケンス = 2 |
| C4 | `vHANDY_SET_POWERPON_SEQ == 3` | パワーオンシーケンス = 3 |
| C5 | `vHANDY_SET_POWERPON_SEQ == 6` | パワーオンシーケンス = 6 |
| C6 | `vHANDY_SET_POWERPON_SEQ == 7` | パワーオンシーケンス = 7 |
| C7 | `vHANDY_SET_POWERPON_SEQ == 8` | パワーオンシーケンス = 8 |
| C8 | `vHANDY_SET_OP_POWER_PUSH == 0` | オープンパワープッシュ = 0 |

## 9つのテストケース

| # | パターン | 期待値 | 検証内容 | 関数名 |
|---|---------|--------|----------|---------|
| 1 | TTFFFFFT | TRUE | ベースラインケース | test_mcdc_case_01_TTFFFFFT |
| 2 | FTFFFFFT | FALSE | C1の独立性 | test_mcdc_case_02_FTFFFFFT |
| 3 | TFFFFFFT | FALSE | OR条件の必要性 | test_mcdc_case_03_TFFFFFFT |
| 4 | TTFFFFFF | FALSE | C8の独立性 | test_mcdc_case_04_TTFFFFFF |
| 5 | TFTFFFFT | TRUE | C3の独立性 | test_mcdc_case_05_TFTFFFFT |
| 6 | TFFTFFFT | TRUE | C4の独立性 | test_mcdc_case_06_TFFTFFFT |
| 7 | TFFFTFFT | TRUE | C5の独立性 | test_mcdc_case_07_TFFFTFFT |
| 8 | TFFFFTFT | TRUE | C6の独立性 | test_mcdc_case_08_TFFFFTFT |
| 9 | TFFFFFTT | TRUE | C7の独立性 | test_mcdc_case_09_TFFFFFTT |

## MC/DC カバレッジ: 100%

全ての条件（C1～C8）が独立して結果に影響を与えることが検証されています。

### 独立性の証明

各条件について、その条件だけを変更することで結果が変わるテストケースのペアが存在します：

- **C1**: Case 1 (T→TRUE) vs Case 2 (F→FALSE)
- **C2**: Case 1 (T→TRUE) vs Case 3 (F→FALSE)
- **C3**: Case 5 (T→TRUE) vs Case 3 (F→FALSE)
- **C4**: Case 6 (T→TRUE) vs Case 3 (F→FALSE)
- **C5**: Case 7 (T→TRUE) vs Case 3 (F→FALSE)
- **C6**: Case 8 (T→TRUE) vs Case 3 (F→FALSE)
- **C7**: Case 9 (T→TRUE) vs Case 3 (F→FALSE)
- **C8**: Case 1 (T→TRUE) vs Case 4 (F→FALSE)

## ファイル構成

```
AutoUniTestGen/
├── test/
│   ├── mcdc_state_fullopen_test.c      # テスト実装
│   └── MCDC_COVERAGE_REPORT.md         # カバレッジレポート
└── doc/
    ├── MCDC_SEQUENCE_DIAGRAM.md        # シーケンス図
    ├── MCDC_CLASS_DIAGRAM.md           # クラス図
    └── MCDC_IMPLEMENTATION_README.md   # このファイル
```

## テスト実行方法

### 前提条件
- Unity テストフレームワークがインストールされていること
- GCC または互換性のあるCコンパイラ

### コンパイル

```bash
gcc -I/path/to/unity/src \
    test/mcdc_state_fullopen_test.c \
    /path/to/unity/src/unity.c \
    -o mcdc_test
```

### 実行

```bash
./mcdc_test
```

### 期待される出力

```
test/mcdc_state_fullopen_test.c:XX:test_mcdc_case_01_TTFFFFFT:PASS
test/mcdc_state_fullopen_test.c:XX:test_mcdc_case_02_FTFFFFFT:PASS
test/mcdc_state_fullopen_test.c:XX:test_mcdc_case_03_TFFFFFFT:PASS
test/mcdc_state_fullopen_test.c:XX:test_mcdc_case_04_TTFFFFFF:PASS
test/mcdc_state_fullopen_test.c:XX:test_mcdc_case_05_TFTFFFFT:PASS
test/mcdc_state_fullopen_test.c:XX:test_mcdc_case_06_TFFTFFFT:PASS
test/mcdc_state_fullopen_test.c:XX:test_mcdc_case_07_TFFFTFFT:PASS
test/mcdc_state_fullopen_test.c:XX:test_mcdc_case_08_TFFFFTFT:PASS
test/mcdc_state_fullopen_test.c:XX:test_mcdc_case_09_TFFFFFTT:PASS

-----------------------
9 Tests 0 Failures 0 Ignored
OK
```

## 設計原則

### 1. 独立性の保証
各テストケースは完全に独立しており、`setUp()` と `tearDown()` で状態をリセットします。

### 2. 明確なネーミング
テスト関数名にパターン（TTFFFFFT等）を含めることで、何をテストしているかが一目瞭然です。

### 3. ドキュメント化
各テストケースに詳細なコメントを付与し、何を検証しているかを明確にしています。

### 4. 保守性
条件が変更された場合でも、容易に対応できる構造になっています。

## 参考規格

- **DO-178C**: 航空機搭載ソフトウェアの認証規格
- **MC/DC**: Modified Condition/Decision Coverage
  - Level A（最高安全性レベル）で要求されるカバレッジ基準

## 変更履歴

| 日付 | バージョン | 変更内容 | 作成者 |
|------|-----------|---------|--------|
| 2025-11-17 | 1.0 | 初版作成 | Claude |

## ライセンス

このドキュメントとテストコードは、プロジェクトのライセンスに従います。

## 関連リンク

- [Unity Testing Framework](https://github.com/ThrowTheSwitch/Unity)
- [DO-178C Standard](https://en.wikipedia.org/wiki/DO-178C)
- [MC/DC Coverage](https://en.wikipedia.org/wiki/Modified_condition/decision_coverage)
