# 関数マクロ対応ガイド

## 概要

C言語単体テスト自動生成ツールが、引数を持つ関数マクロ（Function-like Macros）に対応しました。

```c
#define MACRO(a)   function(a)
#define MAX(a, b)  ((a) > (b) ? (a) : (b))
```

## 対応する関数マクロ

### 基本的な関数マクロ

```c
#define MAX(a, b)  ((a) > (b) ? (a) : (b))
#define MIN(a, b)  ((a) < (b) ? (a) : (b))
#define SQUARE(x)  ((x) * (x))
```

**展開例:**
```c
int result = MAX(10, 20);
↓
int result = ((10) > (20) ? (10) : (20));
```

### 関数呼び出しを含むマクロ

```c
#define CALL_FUNC(x)  process_value(x)
#define ADD_OFFSET(val)  ((val) + 10)
```

**展開例:**
```c
int processed = CALL_FUNC(5);
↓
int processed = process_value(5);
```

### 複数引数を持つマクロ

```c
#define RANGE_CHECK(val, min, max)  ((val) >= (min) && (val) <= (max))
#define CLAMP(val, min, max)  ((val) < (min) ? (min) : ((val) > (max) ? (max) : (val)))
```

**展開例:**
```c
if (RANGE_CHECK(x, 0, 100)) { ... }
↓
if (((x) >= (0) && (x) <= (100))) { ... }
```

### ネストした関数マクロ

マクロの本体内で別の関数マクロを呼び出すことができます。

```c
#define ABS(x)  ((x) < 0 ? -(x) : (x))
#define DIFF(a, b)  ABS((a) - (b))
#define IN_RANGE(val, center, tolerance)  (DIFF((val), (center)) <= (tolerance))
```

**展開例:**
```c
if (IN_RANGE(10, 5, 3)) { ... }
↓
// 3段階の展開
// 1. IN_RANGE → DIFF を呼び出し
// 2. DIFF → ABS を呼び出し
// 3. 最終的な展開結果
if ((((((10)) - ((5))) < 0 ? -(((10)) - ((5))) : (((10)) - ((5)))) <= (3))) { ... }
```

### 条件式を返すマクロ

```c
#define IS_VALID(x)  ((x) >= 0 && (x) <= 255)
#define VALIDATE_AND_PROCESS(x)  (IS_VALID(x) ? SQUARE(x) : -1)
```

## 使用例

### 例1: 基本的な使用

**入力ファイル (test.c):**
```c
#define MAX(a, b)  ((a) > (b) ? (a) : (b))

int calculate(int x, int y) {
    int max_val = MAX(x, y);
    
    if (max_val > 50) {
        return max_val * 2;
    }
    
    return max_val;
}
```

**コマンド:**
```bash
python main.py -i test.c -f calculate -o output
```

**結果:**
- 関数マクロ `MAX(a, b)` が自動検出
- マクロ展開後のコードで解析
- MC/DC真偽表とテストコードを生成

### 例2: 複雑なマクロ

**入力ファイル (complex.c):**
```c
#define ABS(x)  ((x) < 0 ? -(x) : (x))
#define DIFF(a, b)  ABS((a) - (b))
#define IN_RANGE(val, center, tolerance)  (DIFF((val), (center)) <= (tolerance))

int check_range(int value, int target) {
    if (IN_RANGE(value, target, 10)) {
        return 1;
    }
    return 0;
}
```

**コマンド:**
```bash
python main.py -i complex.c -f check_range -o output
```

## 機能の詳細

### 自動検出

ソースコード内の関数マクロ定義を自動的に検出します。

```
[INFO] 🔧 ソースコード内の関数マクロ定義: 7個
[INFO]   ✓ MAX(a, b) = ((a) > (b) ? (a) : (b))
[INFO]   ✓ MIN(a, b) = ((a) < (b) ? (a) : (b))
[INFO]   ✓ SQUARE(x) = ((x) * (x))
```

### 多段階展開

ネストしたマクロも正しく展開されます（最大10段階）。

**展開順序:**
1. 最も外側のマクロから展開開始
2. 展開結果に含まれるマクロを再度展開
3. すべてのマクロが展開されるまで繰り返し

### 引数の括弧対応

引数内に括弧がネストしている場合も正しく処理します。

```c
// 引数に関数呼び出しを含む場合
result = SQUARE(helper_function(x));
↓
result = ((helper_function(x)) * (helper_function(x)));

// 引数に演算を含む場合
result = MAX((a + b), (c - d));
↓
result = (((a + b)) > ((c - d)) ? ((a + b)) : ((c - d)));
```

## ログ出力

関数マクロの処理状況は詳細にログ出力されます。

### 検出時のログ

```
[INFO] 🔧 ソースコード内の関数マクロ定義: 3個
[INFO]   ✓ ABS(x) = ((x) < 0 ? -(x) : (x))
[INFO]   ✓ DIFF(a, b) = ABS((a) - (b))
[INFO]   ✓ IN_RANGE(val, center, tolerance) = (DIFF((val), (center)) <= (tolerance))
[INFO] 📊 使用されるマクロ定義の合計: 0個 (通常) + 3個 (関数)
```

### 展開時のログ（DEBUG レベル）

```bash
python main.py -i test.c -f func --log-level DEBUG
```

```
[DEBUG] 関数マクロ展開: IN_RANGE(10, 5, 3) → (DIFF((10), (5)) <= (3))
[DEBUG] 関数マクロ展開: DIFF((10), (5)) → ABS(((10)) - ((5)))
[DEBUG] 関数マクロ展開: ABS(((10)) - ((5))) → ((((10)) - ((5))) < 0 ? -(((10)) - ((5))) : (((10)) - ((5))))
```

## 制限事項と対応状況

### ✅ 対応済み

- [x] 基本的な関数マクロ（1個以上の引数）
- [x] ネストした関数マクロ（マクロ内でマクロ呼び出し）
- [x] 複数引数（カンマ区切り）
- [x] 引数内の括弧（ネスト）
- [x] 引数内の関数呼び出し
- [x] 条件式を返すマクロ
- [x] 多段階展開（最大10回）

### ⚠️ 未対応

- [ ] 可変長引数マクロ (`#define MACRO(...)`)
- [ ] `#` 演算子（文字列化）
- [ ] `##` 演算子（トークン連結）
- [ ] `__VA_ARGS__`

### 制限事項の詳細

#### 可変長引数マクロ

```c
// 未対応
#define DEBUG_PRINT(fmt, ...)  printf(fmt, __VA_ARGS__)
```

**回避策:** 引数の数を明示的に指定

```c
// 対応可能
#define DEBUG_PRINT_1(fmt, a)  printf(fmt, a)
#define DEBUG_PRINT_2(fmt, a, b)  printf(fmt, a, b)
```

#### トークン操作

```c
// 未対応: # 演算子
#define TO_STRING(x)  #x

// 未対応: ## 演算子
#define CONCAT(a, b)  a##b
```

**回避策:** 通常のマクロとして定義

```c
// 対応可能
#define GET_VALUE(x)  (x)
```

## トラブルシューティング

### 警告: 引数数が一致しません

```
[WARNING] 関数マクロ MACRO の引数数が一致しません: 期待=2, 実際=1
```

**原因:**
- マクロ呼び出し時の引数数がマクロ定義と一致しない

**解決策:**
1. マクロ定義を確認
2. マクロ呼び出しの引数を確認
3. 必要に応じてマクロ定義を修正

### 警告: 最大反復回数に達しました

```
[WARNING] 関数マクロ展開が最大反復回数に達しました。循環参照がある可能性があります。
```

**原因:**
- マクロが循環参照している

```c
// 循環参照の例（避けるべき）
#define A(x)  B(x)
#define B(x)  A(x)
```

**解決策:**
- マクロ定義を見直し、循環参照を解消

## パフォーマンス

### 展開時間

- 単純なマクロ: < 1ms
- ネストしたマクロ（3段階）: < 10ms
- 複雑なマクロ（10段階）: < 50ms

### 推奨事項

1. **マクロのネストは最小限に**
   - 深いネスト（5段階以上）は避ける
   - 可能であれば通常の関数を使用

2. **マクロ名は明確に**
   - 一般的な単語（IS, GET, SET など）は避ける
   - プロジェクト固有のプレフィックスを使用

## 統合ガイド

### 既存プロジェクトでの使用

1. **マクロの整理**
   - プロジェクト内の関数マクロをリストアップ
   - 複雑なマクロは分割を検討

2. **テスト実行**
   ```bash
   # まずは小さなファイルでテスト
   python main.py -i simple.c -f test_func -o output --log-level DEBUG
   
   # 問題なければバッチ処理
   python main.py -b input_files.txt -o output_dir
   ```

3. **結果の検証**
   - 生成されたテストコードを確認
   - マクロ展開が正しいか確認
   - 必要に応じてマクロ定義を調整

## まとめ

関数マクロ対応により、より実践的なC言語プロジェクトで単体テスト自動生成ツールを使用できるようになりました。

**主な利点:**
- 既存コードの変更不要
- 複雑なマクロも自動展開
- MC/DC 100%カバレッジを維持

**推奨用途:**
- 組み込みシステム開発
- レガシーコードのテスト追加
- マクロを多用するプロジェクト

## 関連ドキュメント

- [マクロ・条件付きコンパイルガイド](MACRO_AND_CONDITIONAL_GUIDE.md)
- [プリプロセッサ対応状況](PREPROCESSOR_SUPPORT_STATUS.md)
- [ソースコード定義参照ガイド](SOURCE_DEFINE_REFERENCE_GUIDE.md)
