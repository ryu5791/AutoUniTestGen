# AutoUniTestGen v2.9.0 リリースノート

**リリース日**: 2025-11-21  
**バージョン**: v2.9.0  
**前バージョン**: v2.8.0  

---

## 🎉 主な変更点

### ✨ 新機能
- **ネスト構造体の完全サポート**: 多階層にネストした構造体メンバーのアサーション生成が完全に動作するようになりました
- **2パス処理による型解決**: 構造体定義の相互参照を解決する2パス処理を実装

### 🔧 改善
- **TypedefExtractor.extract_struct_definitions()**: 構造体マップを使用した型参照の解決機能を追加
- **3階層以上のネスト対応**: `pixel_t.position.x`のような深いネスト構造も正しく展開

### 🐛 バグ修正
- ネスト構造体メンバーが`result.position`として生成される問題を修正
- 構造体型メンバーの`nested_struct`プロパティが設定されない問題を修正

---

## 📊 技術的詳細

### 2パス処理の実装
```python
# 第1パス: すべての構造体定義を収集
struct_defs = []
for node in self._walk_ast(ast):
    if self._is_typedef_struct(node):
        struct_def = self._parse_typedef_struct(node, resolve_types=False)
        struct_defs.append(struct_def)

# 構造体マップを作成
struct_map = {s.name: s for s in struct_defs}

# 第2パス: 型参照を解決
for struct_def in struct_defs:
    for member in struct_def.members:
        if member.type in struct_map:
            member.nested_struct = struct_map[member.type]
```

### 動作確認済みテストケース

#### 2階層ネスト構造体
```c
typedef struct {
    uint16_t x;
    uint16_t y;
} point_t;

typedef struct {
    uint8_t id;
    point_t position;  // ネスト
    uint32_t color;
} pixel_t;
```

**生成結果**:
```c
TEST_ASSERT_EQUAL(0, result.id);
TEST_ASSERT_EQUAL(0, result.position.x);  // ✅ 正しく展開
TEST_ASSERT_EQUAL(0, result.position.y);  // ✅ 正しく展開
TEST_ASSERT_EQUAL(0, result.color);
```

#### 3階層ネスト構造体
```c
typedef struct {
    coord_t position;  // 2階層目
    rgb_t color;       // 2階層目
} pixel_info_t;

typedef struct {
    uint8_t id;
    pixel_info_t info;  // 3階層のネスト
    uint32_t timestamp;
} display_element_t;
```

**生成結果**:
```c
TEST_ASSERT_EQUAL(0, result.id);
TEST_ASSERT_EQUAL(0, result.info.position.x);  // ✅ 3階層展開
TEST_ASSERT_EQUAL(0, result.info.position.y);  // ✅ 3階層展開
TEST_ASSERT_EQUAL(0, result.info.color.r);     // ✅ 3階層展開
TEST_ASSERT_EQUAL(0, result.info.color.g);     // ✅ 3階層展開
TEST_ASSERT_EQUAL(0, result.info.color.b);     // ✅ 3階層展開
TEST_ASSERT_EQUAL(0, result.timestamp);
```

---

## 📁 変更されたファイル

### 修正されたファイル
- `src/parser/typedef_extractor.py`
  - `extract_struct_definitions()`: 2パス処理に変更
  - `_parse_typedef_struct()`: resolve_typesパラメータを追加
  - `_parse_direct_struct()`: resolve_typesパラメータを追加

### 追加されたテストケース
- `test_cases/test_deep_nested_struct.c`: 3階層ネスト構造体のテスト

---

## 🧪 テスト結果

| テストケース | 結果 | 備考 |
|------------|------|------|
| test_simple_struct.c | ✅ | 単純な構造体 |
| test_nested_struct.c | ✅ | 2階層ネスト |
| test_deep_nested_struct.c | ✅ | 3階層ネスト |
| test_bitfield_struct.c | ✅ | ビットフィールド |

---

## 🚀 使用方法

```bash
# 基本的な使用方法（変更なし）
python3 main.py -i source.c -f function_name -o output_dir

# ネスト構造体のテスト
python3 main.py -i test_cases/test_nested_struct.c -f get_pixel -o output/test
```

---

## 📝 既知の問題

### 未実装機能
- ポインタメンバーの詳細なアサーション生成
- 配列メンバーの詳細なアサーション生成
- 共用体（union）のサポート

これらの機能は今後のバージョンで実装予定です。

---

## 🔄 アップグレード手順

v2.8.0からv2.9.0へのアップグレード:
1. 新しいバージョンのファイルをダウンロード
2. 既存のディレクトリを置き換え
3. 特別な設定変更は不要

---

## 📚 関連ドキュメント

- [クラス図 v2.8.0](design_class_diagram_v2_8_0.md) - 基本構造は変更なし
- [シーケンス図 v2.8.0](design_sequence_diagram_v2_8_0.md) - 2パス処理が追加
- [引継ぎ資料](HANDOFF_COMPLETE_v2_8_0_to_v2_9_0.md)

---

**開発者**: AutoUniTestGen Development Team  
**問い合わせ**: [プロジェクトページ]
