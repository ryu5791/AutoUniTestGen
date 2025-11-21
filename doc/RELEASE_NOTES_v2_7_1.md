# AutoUniTestGen v2.7.1 リリースノート

**リリース日**: 2025-11-20  
**バージョン**: 2.7.1

---

## 🎯 このリリースについて

v2.7.1は、構造体型戻り値のアサーション生成における重要な修正を含むバグフィックスリリースです。

---

## 🐛 修正された問題

### 1. 構造体型戻り値のアサーション生成エラー

**問題**:
```c
void test_func(void) {
    state_def_t result = {0};
    result = test_func();
    
    // ❌ エラー: 構造体を整数と比較
    TEST_ASSERT_EQUAL(0, result);
}
```

**修正後**:
```c
void test_func(void) {
    state_def_t result = {0};
    result = test_func();
    
    // ✅ 正しい: TODOコメントで案内
    // 結果を確認
    // TODO: 期待値を設定してください
    // 例: TEST_ASSERT_EQUAL(expected_value, result.member_name);
}
```

### 2. エンコーディングエラー

**問題**: Shift_JISでエンコードできない文字がある場合にファイル保存が失敗

**修正**: UTF-8エンコーディングに変更

---

## ✨ 新機能・改善

### 1. 構造体型判定機能の追加

**新メソッド**: `TestFunctionGenerator._is_struct_type()`

構造体型かどうかを以下の基準で判定：
- `_t` で終わる（typedef structの命名規則）
- 大文字で始まる（カスタム型の命名規則）
- `struct` キーワードが含まれる

```python
def _is_struct_type(self, type_name: str) -> bool:
    """
    型が構造体かどうかを判定
    
    判定基準:
    1. _t で終わる（typedef struct の命名規則）
    2. 大文字で始まる（カスタム型の命名規則）
    3. 'struct' キーワードが含まれる
    """
```

### 2. アサーション生成ロジックの改善

戻り値の型に応じて適切なアサーションを生成：

**構造体型の場合**:
```c
// TODO: 期待値を設定してください
// 例: TEST_ASSERT_EQUAL(expected_value, result.member_name);
```

**基本型の場合**:
```c
TEST_ASSERT_EQUAL(expected_value, result);
```

### 3. UTF-8エンコーディング対応

`TestCode.save()` メソッドをUTF-8エンコーディングに変更し、日本語やその他のUnicode文字を含むコードの生成を安定化。

---

## 📝 変更されたファイル

### 修正されたファイル

1. **src/test_generator/test_function_generator.py**
   - `_is_struct_type()` メソッドを追加
   - `_generate_assertions()` メソッドを修正
     - 構造体型判定を追加
     - 構造体の場合はTODOコメントを生成
     - 基本型の場合は従来通りのアサーション生成

2. **src/data_structures.py**
   - `TestCode.save()` メソッドのエンコーディングをShift_JISからUTF-8に変更

3. **VERSION**
   - 2.6.6 → 2.7.1 に更新

### 更新されたドキュメント

1. **doc/design_class_diagram.md**
   - v2.7用にクラス図を更新
   - 構造体判定機能を追加

2. **doc/design_sequence_diagram.md**
   - v2.7用にシーケンス図を更新
   - 構造体型アサーション生成フローを追加

---

## 🧪 テスト結果

### テストケース1: 構造体を返す関数

**入力ファイル** (`test_struct_return.c`):
```c
typedef struct {
    uint8_t status;
    uint16_t value;
} state_def_t;

state_def_t test_func(int input) {
    if (input > 0) {
        result.status = 1;
        result.value = 100;
    } else {
        result.status = 0;
        result.value = 0;
    }
    return result;
}
```

**生成されたテストコード**:
```c
void test_01_input_gt_0_T(void) {
    // 変数を初期化
    state_def_t result = {0};
    int input = 1;
    
    // 対象関数を実行
    result = test_func(input);
    
    // 結果を確認
    // TODO: 期待値を設定してください
    // 例: TEST_ASSERT_EQUAL(expected_value, result.member_name);
}
```

✅ **結果**: TODOコメントが正しく生成され、コンパイルエラーなし

### テストケース2: 基本型を返す関数

**入力ファイル** (`test_basic_return.c`):
```c
int add(int a, int b) {
    if (a > 0) {
        return a + b;
    }
    return 0;
}
```

**生成されたテストコード**:
```c
void test_01_a_gt_0_T(void) {
    // 変数を初期化
    int result = 0;
    int a = 1;
    int b = 0;
    
    // 対象関数を実行
    result = add(a, b);
    
    // 結果を確認
    // TODO: 期待値を設定してください
    TEST_ASSERT_EQUAL(1, result);
}
```

✅ **結果**: アサーションが正しく生成され、従来通りの動作を確認

---

## 🔄 互換性

### 後方互換性

✅ **完全な後方互換性を維持**

- 基本型を返す関数のテスト生成は従来通り動作
- 既存のプロジェクトは変更なしで動作
- コマンドライン引数やAPIに変更なし

### 前方互換性

⚠️ **UTF-8エンコーディングへの変更**

- 生成されるテストコードファイルのエンコーディングがShift_JISからUTF-8に変更
- 既存のツールチェーンがShift_JISを前提としている場合は調整が必要

---

## 📊 パフォーマンス

処理時間への影響はありません：
- 構造体型判定は軽量な文字列パターンマッチング
- アサーション生成ロジックの複雑度は変わらず

---

## 🔮 将来のバージョンでの対応予定

### v2.8以降での機能拡張候補

1. **構造体メンバー情報の抽出**
   - ASTから構造体定義を完全に解析
   - `ParsedData.struct_definitions`フィールドを活用

2. **自動メンバーアサーション生成**
   - 構造体のメンバーごとに自動的にアサーションを生成
   ```c
   TEST_ASSERT_EQUAL(expected_status, result.status);
   TEST_ASSERT_EQUAL(expected_value, result.value);
   ```

3. **高度な構造体対応**
   - ネストした構造体
   - 共用体（union）
   - ビットフィールドを含む構造体

---

## 📋 既知の制限事項

1. **構造体メンバーの自動抽出は未実装**
   - 現在はTODOコメントで案内のみ
   - ユーザーが手動でメンバーごとのアサーションを記述する必要がある

2. **構造体の判定基準**
   - 命名規則に基づく推測的な判定
   - 非標準的な型名の場合、誤判定の可能性がある

---

## 🚀 使用方法

### インストール

```bash
tar -xzf AutoUniTestGen_v2_7_1.tar.gz
cd AutoUniTestGen_v2_7_1
```

### 基本的な使用方法

```bash
# すべて生成（真偽表、テストコード、I/O表）
python3 main.py -i sample.c -f calculate -o output

# 構造体を返す関数のテスト生成
python3 main.py -i struct_return.c -f get_state -o output
```

### 生成されたテストコードの修正

構造体を返す関数の場合、TODOコメントに従ってアサーションを追加：

```c
// 生成されたコード
// TODO: 期待値を設定してください
// 例: TEST_ASSERT_EQUAL(expected_value, result.member_name);

// 修正例
TEST_ASSERT_EQUAL(1, result.status);
TEST_ASSERT_EQUAL(100, result.value);
```

---

## 🐛 バグ報告

バグを発見した場合は、以下の情報を含めて報告してください：
- バージョン情報
- 入力ファイル（C言語ソースコード）
- 実行したコマンド
- エラーメッセージ
- 期待される動作

---

## 👥 貢献者

- ichiryu - プロジェクトオーナー、主要開発者
- Claude (Anthropic) - 開発支援

---

## 📄 ライセンス

このプロジェクトのライセンス情報については、プロジェクトルートのLICENSEファイルを参照してください。

---

**次のバージョン予定**: v2.8.0
- 構造体メンバー情報の完全な抽出
- 自動メンバーアサーション生成

---

**作成日**: 2025-11-20  
**作成者**: AutoUniTestGen Development Team  
**バージョン**: 2.7.1  
**状態**: ✅ リリース済み
