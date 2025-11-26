# AutoUniTestGen v2.10.1 リリースノート

**リリース日**: 2025-11-21  
**前バージョン**: v2.10.0  

## 🎯 概要

バージョン2.10.1では、出力ファイルのエンコーディングをShift-JISに変更し、日本の開発環境での互換性を向上させました。設定ファイルから出力エンコーディングを柔軟に変更できるようになりました。

## ✨ 新機能

### 1. 🌐 Shift-JIS出力対応
- デフォルトの出力エンコーディングをShift-JISに変更
- 日本のWindows環境や組み込み開発環境との互換性向上
- Visual Studioなどの日本語版IDEで文字化けなく開ける

### 2. 🔧 設定可能な出力エンコーディング
- `config.ini`で出力エンコーディングを設定可能
- 対応エンコーディング: shift_jis, utf-8, cp932, euc-jp など

## 🔧 技術的詳細

### エンコーディング処理フロー

```
[入力Cソース（自動検出）]
    ↓
[内部処理（Python文字列）]
    ↓
[出力（設定されたエンコーディング）]
    ├── テストコード (.c) → Shift-JIS
    ├── 真偽表 (.xlsx) → Excel内部形式
    └── I/O表 (.xlsx) → Excel内部形式
```

### 設定ファイル（config.ini）

```ini
[output]
# 出力ファイルのエンコーディング（utf-8, shift_jis, cp932, euc-jp など）
output_encoding = shift_jis
```

### 実装詳細

1. **新規モジュール**: `src/encoding_config.py`
   - 設定ファイルからエンコーディングを読み込み
   - グローバル設定として管理

2. **修正されたファイル**:
   - `src/data_structures.py`: TestCode.save()メソッドが設定を使用
   - `src/c_test_auto_generator.py`: スタンドアロンモードも設定を使用
   - `config.ini`: output_encoding設定を追加

## 📊 動作確認

### テスト結果
```bash
# 日本語コメントを含むファイルのテスト
python3 main.py -i test_japanese.c -f test_function -o output/test

# 生成されたファイルの確認
file output/test/test_test_japanese_test_function.c
# 結果: Non-ISO extended-ASCII text (Shift-JIS)

# 内容確認（Shift-JISからUTF-8に変換して表示）
iconv -f shift_jis -t utf-8 output/test/test_test_japanese_test_function.c
# 結果: 日本語コメントが正しく表示される
```

## 🚀 使用方法

### 基本的な使用方法（変更なし）
```bash
python3 main.py -i input.c -f target_function -o output/
```

### エンコーディングの変更方法

1. **設定ファイルで変更**:
```ini
# config.ini
[output]
output_encoding = utf-8  # UTF-8に変更する場合
```

2. **デフォルト設定**:
- 出力: Shift-JIS（日本環境向け）
- 入力: 自動検出（UTF-8, Shift-JIS, EUC-JP等に対応）

## 📝 既知の問題

現時点で既知の問題はありません。

## 🔄 アップグレード方法

```bash
# 1. 新バージョンを展開
tar -xzf AutoUniTestGen_v2_10_1.tar.gz

# 2. バージョン確認
cat AutoUniTestGen_v2_10_1/VERSION
# 出力: 2.10.1

# 3. 設定ファイルでエンコーディングを確認
grep output_encoding AutoUniTestGen_v2_10_1/config.ini
# 出力: output_encoding = shift_jis
```

## ✅ チェックリスト

- [x] Shift-JIS出力対応
- [x] 設定ファイルからのエンコーディング読み込み
- [x] 日本語コメントの正常な処理
- [x] Windows環境での互換性確認
- [x] Visual Studioでの文字化けなし

## 📊 変更ファイル

| ファイル | 変更内容 |
|----------|----------|
| `src/encoding_config.py` | 新規作成（エンコーディング管理） |
| `src/data_structures.py` | TestCode.save()メソッドを修正 |
| `src/c_test_auto_generator.py` | エンコーディング設定を使用 |
| `config.ini` | output_encoding設定を追加 |
| `VERSION` | 2.10.0 → 2.10.1 |

## 🙏 謝辞

ユーザーからのフィードバックにより、日本の開発環境に適したShift-JIS出力の必要性を認識し、実装することができました。

## 📞 サポート

問題や要望がありましたら、GitHubのIssueでお知らせください。

---

**次期バージョン予定**: v2.11.0
- ポインタメンバーのアサーション生成
- 配列メンバーのアサーション生成
- 共用体（union）のサポート
