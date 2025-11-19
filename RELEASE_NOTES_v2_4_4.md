# AutoUniTestGen v2.4.4 リリースノート

**リリース日**: 2025-11-19  
**対象ユーザー**: すべてのAutoUniTestGenユーザー

---

## 📢 ハイライト

v2.4.4は、メンテナンス性とリソース効率を向上させるアップデートです。

### 主な改善

1. ✨ **標準型定義の外部ファイル化**  
   標準型リストを `standard_types.h` から自動読み込み（34種類対応）

2. ✨ **バージョン管理の自動化**  
   `VERSION` ファイルから動的にバージョンを取得

---

## 🎯 ユーザーへの影響

### 👍 メリット

- **標準型の警告が削減**: `int8_t`, `uint8_t` などの警告が表示されなくなりました
- **バージョン管理が容易に**: `VERSION` ファイルを編集するだけでバージョン変更可能
- **メンテナンス性向上**: 標準型の追加・変更が簡単に

### 🔄 変更が必要な操作

なし（完全な後方互換性あり）

---

## 📥 インストール・アップグレード

### 新規インストール

```bash
tar -xzf AutoUniTestGen_v2_4_4.tar.gz
cd AutoUniTestGen_v2_4_4
pip install -r requirements.txt
```

### 既存バージョンからのアップグレード

```bash
# v2.4.3.1からの移行
tar -xzf AutoUniTestGen_v2_4_4.tar.gz
cd AutoUniTestGen_v2_4_4

# standard_types.hが含まれていることを確認
ls standard_types.h

# 動作確認
python main.py --version
# 出力: c-test-gen 2.4.4
```

---

## 🚀 使用方法

使用方法は従来と変わりません。

### 基本的な使い方

```bash
# すべて生成（真偽表、テストコード、I/O表）
python main.py -i source.c -f function_name -o output_dir

# バージョン確認
python main.py --version

# ヘルプ表示
python main.py -h
```

### 動作確認例

```bash
# 難読化コードでのテスト
python main.py -i 22_難読化_obfuscated.c -f Utf1 -o test_output

# 実行ログで確認:
# [INFO] ... - standard_types.hから34個の標準型を読み込みました
```

---

## 📋 新機能の詳細

### 1. 標準型定義の外部ファイル化

**概要**:  
従来はソースコード内にハードコードされていた標準型リストを、`standard_types.h` から読み込むように変更しました。

**対応する標準型（34種類）**:
- `int8_t` ~ `uint64_t` (8種類)
- `int_least8_t` ~ `uint_least64_t` (8種類)
- `int_fast8_t` ~ `uint_fast64_t` (8種類)
- `intmax_t`, `uintmax_t`, `intptr_t`, `uintptr_t`
- `size_t`, `ssize_t`, `ptrdiff_t`, `wchar_t`, `wint_t`, `bool`

**実行ログの変化**:
```
[INFO] 2025-11-19 00:47:27 - src.parser.typedef_extractor - standard_types.hから34個の標準型を読み込みました
```

**カスタマイズ方法**:  
プロジェクト固有の標準型を追加する場合は、`standard_types.h` に typedef を追加してください。

```c
// standard_types.h に追加
typedef int my_custom_int_t;
```

### 2. バージョン番号の動的取得

**概要**:  
バージョン番号を `VERSION` ファイルから自動的に読み込みます。

**使用例**:
```bash
$ cat VERSION
2.4.4

$ python main.py --version
c-test-gen 2.4.4

# バージョンを変更する場合
$ echo "2.9.9" > VERSION

$ python main.py --version
c-test-gen 2.9.9
```

---

## 🐛 既知の問題

現在のところ、既知の問題はありません。

---

## 📈 パフォーマンス

処理速度やメモリ使用量に変化はありません。

---

## 🔜 今後の予定

### v2.5.0（計画中）

- MC/DC 100%達成のためのpcpp統合
- プリプロセッサディレクティブの完全展開
- より多くの条件式抽出による網羅的なテストケース生成

---

## 💬 フィードバック

バグ報告や機能要望は、プロジェクトリポジトリの Issue にてお願いします。

---

## 📚 ドキュメント

- [パッチノート（詳細）](./PATCH_NOTES_v2_4_4.md)
- [統合引継ぎ資料](./HANDOFF_v2_4_3_1_INTEGRATED.md)
- [使用方法](./README.md)（従来と変更なし）

---

**v2.4.4をお楽しみください！**
