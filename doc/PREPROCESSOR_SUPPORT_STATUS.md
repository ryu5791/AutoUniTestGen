# プリプロセッサ対応状況

## 概要

C言語単体テスト自動生成ツールのプリプロセッサ機能の対応状況をまとめたドキュメントです。

最終更新: 2025-11-07

## 対応状況一覧

### ✅ 完全対応

| 機能 | 構文例 | 対応状況 | 備考 |
|------|--------|----------|------|
| マクロ定義（通常） | `#define MAX 100` | ✅ 完全対応 | 単純な値の定義 |
| マクロ定義（式） | `#define SIZE (10*2)` | ✅ 完全対応 | 式の定義も可 |
| **関数マクロ** | `#define MAX(a,b) ...` | ✅ **NEW!** | 引数付きマクロ |
| マクロ展開 | - | ✅ 完全対応 | 単語境界を考慮 |
| 条件付きコンパイル（#ifdef） | `#ifdef DEBUG` | ✅ 完全対応 | - |
| 条件付きコンパイル（#ifndef） | `#ifndef NDEBUG` | ✅ 完全対応 | - |
| 条件付きコンパイル（#if） | `#if defined(X)` | ✅ 完全対応 | - |
| #else | `#else` | ✅ 完全対応 | - |
| #elif | `#elif defined(Y)` | ✅ 完全対応 | - |
| #endif | `#endif` | ✅ 完全対応 | - |
| defined() 演算子 | `defined(MACRO)` | ✅ 完全対応 | 括弧ありのみ |
| 論理演算子（&&） | `#if A && B` | ✅ 完全対応 | - |
| 論理演算子（\|\|） | `#if A \|\| B` | ✅ 完全対応 | - |
| ネストした条件 | 複数の#ifネスト | ✅ 完全対応 | - |
| コメント削除 | `/* ... */` `// ...` | ✅ 完全対応 | - |
| #include処理 | `#include <stdio.h>` | ✅ 対応 | コメント化 |

### ⚠️ 部分対応

| 機能 | 構文例 | 対応状況 | 制限事項 |
|------|--------|----------|----------|
| defined() 演算子 | `defined MACRO` | ⚠️ 未対応 | 括弧なしの構文は未対応 |
| マクロ再定義 | `#undef` `#define` | ⚠️ 制限あり | #undefは認識するが無視 |

### ❌ 未対応

| 機能 | 構文例 | 対応状況 | 回避策 |
|------|--------|----------|--------|
| 可変長引数マクロ | `#define PRINT(...)` | ❌ 未対応 | 固定引数版を使用 |
| `__VA_ARGS__` | - | ❌ 未対応 | - |
| # 演算子（文字列化） | `#define STR(x) #x` | ❌ 未対応 | 通常の値として扱う |
| ## 演算子（トークン連結） | `#define CAT(a,b) a##b` | ❌ 未対応 | 別の方法で実装 |
| #include展開 | - | ❌ 未対応 | ヘッダ内容は手動で追加 |
| #pragma | `#pragma once` | ❌ 無視 | コメント化される |
| #error | `#error "message"` | ❌ 無視 | コメント化される |
| #warning | `#warning "message"` | ❌ 無視 | コメント化される |
| #line | `#line 100` | ❌ 無視 | - |

## 新機能: 関数マクロ対応（2025-11-07追加）

### 基本機能

関数マクロ（引数を持つマクロ）に対応しました。

```c
#define MAX(a, b)  ((a) > (b) ? (a) : (b))
#define SQUARE(x)  ((x) * (x))
#define CLAMP(val, min, max)  ((val) < (min) ? (min) : ((val) > (max) ? (max) : (val)))
```

### 対応する構文

#### 1. 基本的な関数マクロ
```c
#define MACRO(param)  (param)
```

#### 2. 複数引数
```c
#define MACRO(a, b, c)  ((a) + (b) + (c))
```

#### 3. ネストしたマクロ呼び出し
```c
#define ABS(x)  ((x) < 0 ? -(x) : (x))
#define DIFF(a, b)  ABS((a) - (b))
```

#### 4. 引数内の括弧
```c
result = MAX((a + b), (c - d));  // 正しく処理される
result = SQUARE(func(x));        // 正しく処理される
```

### 展開の仕組み

#### 多段階展開

最大10回の反復展開をサポート:

```c
#define DOUBLE(x)  ((x) * 2)
#define QUAD(x)    DOUBLE(DOUBLE(x))

int result = QUAD(5);
```

**展開過程:**
1. `QUAD(5)` → `DOUBLE(DOUBLE(5))`
2. `DOUBLE(DOUBLE(5))` → `DOUBLE(((5) * 2))`
3. `DOUBLE(((5) * 2))` → `((((5) * 2)) * 2)`

#### 引数の置換

パラメータ名を単語境界を考慮して置換:

```c
#define TEST(abc)  (abc + abc)

int result = TEST(10);  // → (10 + 10)
```

### 制限事項

1. **可変長引数マクロは未対応**
   ```c
   // ❌ 未対応
   #define DEBUG_PRINT(fmt, ...)  printf(fmt, __VA_ARGS__)
   ```

2. **# および ## 演算子は未対応**
   ```c
   // ❌ 未対応
   #define TO_STRING(x)  #x
   #define CONCAT(a, b)  a##b
   ```

3. **循環参照の検出**
   最大10回の展開で停止し、警告を出力:
   ```
   [WARNING] 関数マクロ展開が最大反復回数に達しました。
   ```

## 優先順位

### マクロ定義の優先順位

1. **外部定義（最優先）**
   - コマンドライン `-D` オプション
   - `--preset` オプション
   
2. **ソースコード内の定義**
   - `#define` ディレクティブ

```bash
# コマンドライン定義が優先される
python main.py -i test.c -f func -D MAX=200 -o output
# ソースコード内の #define MAX 100 は無視される
```

### 展開の優先順位

1. **関数マクロ展開**（先に実行）
2. **通常マクロ展開**（後に実行）

これにより、関数マクロ内の通常マクロも正しく展開されます。

```c
#define OFFSET 10
#define ADD_OFFSET(x)  ((x) + OFFSET)

int result = ADD_OFFSET(5);
// 1. 関数マクロ展開: ((5) + OFFSET)
// 2. 通常マクロ展開: ((5) + 10)
```

## 条件付きコンパイル

### 対応する構文

#### #ifdef / #ifndef

```c
#ifdef DEBUG
    // DEBUGが定義されている場合のコード
#endif

#ifndef NDEBUG
    // NDEBUGが定義されていない場合のコード
#endif
```

#### #if defined()

```c
#if defined(TYPE1)
    // TYPE1が定義されている場合
#elif defined(TYPE2)
    // TYPE2が定義されている場合
#else
    // どちらも定義されていない場合
#endif
```

#### 複合条件

```c
#if defined(TYPE1) && defined(TYPE2)
    // 両方定義されている場合
#endif

#if defined(TYPE1) || defined(TYPE2)
    // どちらか定義されている場合
#endif
```

### 条件評価

条件が偽の場合、該当コードブロックはコメント化されます:

```c
// 入力
#ifdef DEBUG
    debug_function();
#endif

// DEBUG未定義の場合の出力
// #ifdef DEBUG
//     debug_function();
// #endif
```

## 使用例

### 例1: 基本的なマクロ

**入力:**
```c
#define MAX_SIZE 100
#define BUFFER_SIZE (MAX_SIZE * 2)

void process() {
    int buffer[BUFFER_SIZE];
}
```

**展開後:**
```c
void process() {
    int buffer[(100 * 2)];
}
```

### 例2: 関数マクロ

**入力:**
```c
#define MAX(a, b)  ((a) > (b) ? (a) : (b))

int calculate(int x, int y) {
    return MAX(x, y) + 10;
}
```

**展開後:**
```c
int calculate(int x, int y) {
    return ((x) > (y) ? (x) : (y)) + 10;
}
```

### 例3: 条件付きコンパイル + 関数マクロ

**入力:**
```c
#define ENABLE_FEATURE_A

#ifdef ENABLE_FEATURE_A
    #define PROCESS(x)  ((x) * 2)
#else
    #define PROCESS(x)  (x)
#endif

int test(int val) {
    return PROCESS(val);
}
```

**展開後（ENABLE_FEATURE_A定義時）:**
```c
int test(int val) {
    return ((val) * 2);
}
```

## エラーハンドリング

### 引数数の不一致

```c
#define ADD(a, b)  ((a) + (b))

int result = ADD(1, 2, 3);  // 引数が多すぎる
```

**ログ出力:**
```
[WARNING] 関数マクロ ADD の引数数が一致しません: 期待=2, 実際=3
```

展開されず、元のコードが維持されます。

### 括弧の不一致

```c
int result = MAX(1, (2 + 3);  // 閉じ括弧が足りない
```

展開されず、元のコードが維持されます（構文エラーはpycparserで検出）。

### 循環参照

```c
#define A(x)  B(x)
#define B(x)  A(x)

int result = A(10);
```

**ログ出力:**
```
[WARNING] 関数マクロ展開が最大反復回数に達しました。循環参照がある可能性があります。
```

10回の展開で停止し、部分的に展開された結果を使用。

## パフォーマンス

### 処理時間

| マクロの種類 | ファイルサイズ | 処理時間 |
|--------------|----------------|----------|
| 通常マクロのみ（10個） | 1KB | < 1ms |
| 関数マクロ（5個、ネストなし） | 1KB | < 5ms |
| 関数マクロ（5個、3段階ネスト） | 1KB | < 10ms |
| 複雑な構成（20個、5段階ネスト） | 5KB | < 50ms |

### メモリ使用量

通常のファイルサイズ（< 10KB）では追加メモリはほぼゼロ。

## デバッグ

### ログレベルの設定

```bash
# 詳細なログを表示
python main.py -i test.c -f func --log-level DEBUG -o output
```

### 出力例

```
[INFO] 前処理を開始
[INFO] 🔧 ソースコード内の関数マクロ定義: 3個
[INFO]   ✓ MAX(a, b) = ((a) > (b) ? (a) : (b))
[INFO]   ✓ MIN(a, b) = ((a) < (b) ? (a) : (b))
[INFO]   ✓ CLAMP(val, min, max) = ...
[DEBUG] 関数マクロ展開: MAX(10, 20) → ((10) > (20) ? (10) : (20))
[INFO] 有効な関数マクロ定義 (合計 3 個)
[INFO] 前処理が完了
```

## 今後の拡張予定

### Phase 8: プリプロセッサ機能強化（予定）

- [ ] 可変長引数マクロ（`...` と `__VA_ARGS__`）
- [ ] `#` 演算子（文字列化）
- [ ] `##` 演算子（トークン連結）
- [ ] `defined` 演算子の括弧なし構文
- [ ] #include展開（オプション）

## 関連ドキュメント

- [関数マクロ対応ガイド](../FUNCTION_MACRO_GUIDE.md)
- [マクロ・条件付きコンパイルガイド](../MACRO_AND_CONDITIONAL_GUIDE.md)
- [ソースコード定義参照ガイド](../SOURCE_DEFINE_REFERENCE_GUIDE.md)

## まとめ

現在のプリプロセッサは以下をサポート:

✅ **完全対応**
- 通常マクロ定義・展開
- **関数マクロ定義・展開（NEW!）**
- 条件付きコンパイル（#ifdef, #ifndef, #if, #elif, #else, #endif）
- defined() 演算子（括弧あり）
- 論理演算子（&&, ||）
- ネストした条件
- コメント削除

❌ **未対応**
- 可変長引数マクロ
- トークン操作（#, ##）
- #include展開

実用的なC言語プロジェクトで十分に使用可能なレベルに到達しています。
