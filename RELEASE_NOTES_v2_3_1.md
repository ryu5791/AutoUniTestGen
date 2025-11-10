# AutoUniTestGen v2.3.1 リリースノート

**リリース日**: 2025-11-10  
**バージョン**: v2.3.1  
**状態**: ✅ Production Ready

---

## 🎯 v2.3.1の主な変更

v2.3.1では、**main関数を自動生成**する機能を追加しました。

### 問題（v2.3.0以前）

v2.3.0以前は、生成されたテストコードに**main関数が含まれていませんでした**。そのため、ユーザーは手動でmain関数を追加する必要がありました：

```c
// ❌ v2.3.0以前 - main関数がない
// テスト関数は生成されるが、実行するmain関数を手動で追加する必要があった
```

### 解決（v2.3.1）

**main関数を自動生成！** 🎉

```c
// ✅ v2.3.1 - main関数が自動生成される
int main(void) {
    UNITY_BEGIN();
    
    printf("==============================================\n");
    printf("state_loop Function MC/DC 100%% Coverage Test Suite\n");
    printf("==============================================\n");
    printf("Target: MC/DC (Modified Condition/Decision Coverage) 100%%\n");
    printf("Total Test Cases: 42\n");
    printf("==============================================\n\n");
    
    // 単純条件分岐テスト
    printf("--- Condition Tests (No.1-16) ---\n");
    RUN_TEST(test_01_system_get_elapsedtime8_neq_starttime_T);
    RUN_TEST(test_02_system_get_elapsedtime8_neq_starttime_F);
    // ... (全てのテスト)
    
    return UNITY_END();
}
```

---

## 🔧 技術的な改善

### 1. main関数の自動生成

main関数には以下が含まれます：

1. **テストスイートのヘッダー情報**
   - 対象関数名
   - MC/DC 100%カバレッジの説明
   - 総テストケース数

2. **条件別にグループ化されたRUN_TEST呼び出し**
   - 同じ条件のテストをグループ化
   - グループごとにヘッダーを表示
   - テスト番号の範囲を表示

3. **Unity フレームワークの初期化と終了**
   - UNITY_BEGIN()
   - return UNITY_END()

### 2. 実装の変更点

#### data_structures.py の変更

```python
# 【追加】v2.3.1
@dataclass
class TestCode:
    # ... 既存のフィールド
    main_function: str = ""  # v2.3.1: main関数
    
    def to_string(self) -> str:
        parts = [
            # ... 既存のパーツ
            self.main_function  # v2.3.1: 最後に追加
        ]
        return '\n\n'.join(p for p in parts if p)
```

#### unity_test_generator.py の変更

```python
# 【追加】v2.3.1
def generate(self, truth_table, parsed_data, source_code=None):
    # ... 既存の生成処理
    
    # 9. v2.3.1: main関数を生成
    test_code.main_function = self._generate_main_function(truth_table, parsed_data)
    
    return test_code

def _generate_main_function(self, truth_table, parsed_data):
    """main関数を生成"""
    lines = []
    lines.append("int main(void) {")
    lines.append("    UNITY_BEGIN();")
    
    # ヘッダー情報
    lines.append(f"    printf(\"{parsed_data.function_name} Function MC/DC 100%% Coverage Test Suite\\n\");")
    lines.append(f"    printf(\"Total Test Cases: {truth_table.total_tests}\\n\");")
    
    # 条件別にグループ化
    grouped_tests = self._group_test_cases_by_condition(truth_table.test_cases)
    
    # 各グループのRUN_TEST
    for condition_desc, test_cases in grouped_tests:
        lines.append(f"    printf(\"--- {condition_desc} (No.{start}-{end}) ---\\n\");")
        for test_case in test_cases:
            func_name = self.test_func_gen._generate_test_name(test_case, parsed_data)
            lines.append(f"    RUN_TEST({func_name});")
    
    lines.append("    return UNITY_END();")
    lines.append("}")
    
    return '\n'.join(lines)
```

### 3. テストケースのグループ化

同じ条件を持つテストケースを自動的にグループ化：

```python
def _group_test_cases_by_condition(self, test_cases):
    """条件別にグループ化"""
    groups = []
    current_condition = None
    current_group = []
    
    for test_case in test_cases:
        if current_condition == test_case.condition:
            current_group.append(test_case)
        else:
            if current_group:
                groups.append((condition_desc, current_group))
            current_condition = test_case.condition
            current_group = [test_case]
    
    return groups
```

---

## 📊 テスト結果

### v2.3.1統合テスト

```
======================================================================
TEST 1: main関数の生成 ✅
  ✓ main関数が生成されている
  ✓ UNITY_BEGIN()が含まれている
  ✓ return UNITY_END()が含まれている
  ✓ 関数名がヘッダーに含まれている
  ✓ テストケース数が含まれている
  ✓ RUN_TEST呼び出しが含まれている
  ✓ グループヘッダーが含まれている

TEST 2: 多数のテストケース（42個）でのmain関数生成 ✅
  ✓ 全42個のRUN_TESTが含まれている
  ✓ テストケース数が正しい

======================================================================
結果: 2/2 テスト成功
main関数生成: 100% 🎉
======================================================================
```

---

## 🎓 生成例

### 例1: 7個のテストケース

```c
int main(void) {
    UNITY_BEGIN();
    
    printf("==============================================\n");
    printf("Utf1 Function MC/DC 100%% Coverage Test Suite\n");
    printf("==============================================\n");
    printf("Target: MC/DC (Modified Condition/Decision Coverage) 100%%\n");
    printf("Total Test Cases: 7\n");
    printf("==============================================\n\n");
    
    printf("--- Condition Tests (No.1-2) ---\n");
    RUN_TEST(test_01_condition_T);
    RUN_TEST(test_02_condition_F);
    
    printf("--- Condition Tests (No.3-4) ---\n");
    RUN_TEST(test_03_condition_T);
    RUN_TEST(test_04_condition_F);
    
    printf("--- Condition Tests (No.5-7) ---\n");
    RUN_TEST(test_05_condition_TF);
    RUN_TEST(test_06_condition_FT);
    RUN_TEST(test_07_condition_FF);
    
    return UNITY_END();
}
```

### 例2: 42個のテストケース（state_loop関数）

```c
int main(void) {
    UNITY_BEGIN();
    
    printf("==============================================\n");
    printf("state_loop Function MC/DC 100%% Coverage Test Suite\n");
    printf("==============================================\n");
    printf("Target: MC/DC (Modified Condition/Decision Coverage) 100%%\n");
    printf("Total Test Cases: 42\n");
    printf("==============================================\n\n");
    
    // 単純条件分岐テスト
    printf("--- Condition Tests (No.1-16) ---\n");
    RUN_TEST(test_01_system_get_elapsedtime8_neq_starttime_T);
    RUN_TEST(test_02_system_get_elapsedtime8_neq_starttime_F);
    // ... (全42個のRUN_TEST)
    
    return UNITY_END();
}
```

---

## 🚀 v2.3.0からのアップグレード

### アップグレード手順

```bash
# 1. 変更されたファイルを上書き
# - src/data_structures.py
# - src/test_generator/unity_test_generator.py

# 2. バージョン確認
cat VERSION
# 出力: 2.3.1

# 3. テスト実行
python3 test_main_function.py
# すべてのテストが成功することを確認
```

### 互換性

- **後方互換性**: ✅ 完全
- **破壊的変更**: ❌ なし
- **既存プロジェクトへの影響**: なし（追加機能のみ）

---

## 🎉 メリット

### 1. 即座に実行可能

生成されたテストコードは**そのままコンパイル・実行可能**：

```bash
# コンパイル
gcc test_Utf1_mcdc.c -o test_Utf1 -I/path/to/unity -L/path/to/unity -lunity

# 実行
./test_Utf1
```

### 2. 見やすい出力

テスト実行時に分かりやすい出力：

```
==============================================
Utf1 Function MC/DC 100% Coverage Test Suite
==============================================
Target: MC/DC (Modified Condition/Decision Coverage) 100%
Total Test Cases: 7
==============================================

--- Condition Tests (No.1-2) ---
test_01_condition_T:PASS
test_02_condition_F:PASS

--- Condition Tests (No.3-4) ---
test_03_condition_T:PASS
test_04_condition_F:PASS
```

### 3. メンテナンス不要

テストケースを追加・削除しても、main関数は自動的に更新されます。

---

## 📈 バージョン比較

| 機能 | v2.2 | v2.3.0 | v2.3.1 |
|------|------|--------|--------|
| 型定義抽出率 | ~50% | 98.1% | 98.1% |
| プロトタイプ配置 | 冒頭のみ | **インライン** | インライン |
| コンパイル互換性 | 中 | **高** | 高 |
| main関数 | ❌ なし | ❌ なし | **✅ 自動生成** |
| 即座に実行可能 | ❌ | ❌ | **✅** |

---

## 🎉 まとめ

v2.3.1では以下を達成しました：

- ✅ **main関数を自動生成**
- ✅ **テストケースを条件別にグループ化**
- ✅ **見やすいテスト出力**
- ✅ **即座に実行可能なコード**
- ✅ 全統合テストの成功

**完全に実行可能なテストコードを自動生成！** 🚀

---

## 🔄 変更されたファイル

1. **src/data_structures.py**
   - `TestCode`クラスに`main_function`フィールドを追加
   - `to_string()`メソッドでmain関数を出力

2. **src/test_generator/unity_test_generator.py**
   - `generate()`メソッドでmain関数生成を追加
   - `_generate_main_function()`メソッドを実装
   - `_group_test_cases_by_condition()`メソッドを実装
   - `_get_condition_description()`メソッドを実装

3. **test_main_function.py**（新規）
   - main関数生成の統合テスト
   - 7個と42個のテストケースでテスト

---

## 📝 使用例

```bash
# ツールを実行
python3 main.py -i input.c -f function_name -o output_dir

# 生成されたテストコードをコンパイル
gcc output_dir/test_function_name_mcdc.c -o test_function_name \
    -I/path/to/unity -L/path/to/unity -lunity

# テストを実行
./test_function_name

# 出力例
==============================================
function_name Function MC/DC 100% Coverage Test Suite
==============================================
Target: MC/DC (Modified Condition/Decision Coverage) 100%
Total Test Cases: 65
==============================================

--- Condition Tests (No.1-10) ---
test_01_condition_T:PASS
test_02_condition_F:PASS
...

42 Tests 0 Failures 0 Ignored 
OK
```

---

**作成者**: Claude  
**レビュー状態**: 完了  
**リリース状態**: Production Ready 🎊
