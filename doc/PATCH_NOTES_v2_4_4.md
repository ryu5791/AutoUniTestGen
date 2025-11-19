# AutoUniTestGen v2.4.4 パッチノート

**リリース日**: 2025-11-19  
**前バージョン**: v2.4.3.1

---

## 🎯 概要

v2.4.4では、リソース効率向上とメンテナンス性向上を目的とした2つの重要な改善を実装しました。

---

## ✨ 新機能・改善

### 1. 標準型定義の外部ファイル化 🔴

**目的**: ハードコードされた標準型リストをメンテナブルな外部ファイルに移行

**変更内容**:
- `standard_types.h` ファイルの新規作成
- `TypedefExtractor` クラスに `_load_standard_types()` メソッド追加
- 34種類の標準型を自動読み込み（従来は23種類をハードコード）

**影響範囲**:
- `src/parser/typedef_extractor.py`
  - `__init__()`: `self.standard_types` の初期化追加
  - `_load_standard_types()`: 新規メソッド（49行）
  - `_extract_definition_from_source()`: ハードコードされたセットを削除

**メリット**:
- 標準型の追加・変更が容易に
- コードの保守性向上
- ファイルが存在しない場合のフォールバック機能あり

**読み込まれる標準型（34種類）**:
```
int8_t, uint8_t, int16_t, uint16_t, int32_t, uint32_t, int64_t, uint64_t
int_least8_t ~ uint_least64_t (8種類)
int_fast8_t ~ uint_fast64_t (8種類)
intmax_t, uintmax_t, intptr_t, uintptr_t
size_t, ssize_t, ptrdiff_t, wchar_t, wint_t, bool
```

### 2. バージョン番号の動的取得 🟡

**目的**: バージョン管理の一元化とメンテナンス性向上

**変更内容**:
- `get_version()` 関数の実装
- `VERSION` ファイルから自動読み込み
- ハードコードされたバージョン文字列を削除

**影響範囲**:
- `src/cli.py`
  - `get_version()`: 新規関数（14行）
  - `VERSION = get_version()`: 動的取得に変更

**メリット**:
- `VERSION` ファイル更新のみでバージョン変更可能
- コード修正不要
- エラーハンドリング（ファイル未発見時は "unknown" を返す）

---

## 🐛 バグ修正

なし（機能追加のみ）

---

## 🔧 技術的詳細

### TypedefExtractor._load_standard_types()

```python
def _load_standard_types(self) -> Set[str]:
    """standard_types.hから標準型を読み込む"""
    base_path = os.path.dirname(os.path.abspath(__file__))
    std_types_path = os.path.join(base_path, '../../standard_types.h')
    
    standard_types = set()
    
    try:
        with open(std_types_path, 'r', encoding='utf-8') as f:
            for line in f:
                match = re.search(r'typedef\s+.*\s+(\w+)\s*;', line)
                if match:
                    type_name = match.group(1)
                    standard_types.add(type_name)
        
        self.logger.info(f"standard_types.hから{len(standard_types)}個の標準型を読み込みました")
        
    except FileNotFoundError:
        self.logger.warning(f"standard_types.h not found, using fallback")
        # フォールバックの最小セット
        standard_types = { ... }
    
    return standard_types
```

### CLI.get_version()

```python
def get_version() -> str:
    """VERSIONファイルからバージョンを取得"""
    try:
        version_file = Path(__file__).resolve().parent.parent / 'VERSION'
        with open(version_file, 'r', encoding='utf-8') as f:
            return f.read().strip()
    except FileNotFoundError:
        return "unknown"
    except Exception as e:
        print(f"Warning: Failed to read VERSION file: {e}", file=sys.stderr)
        return "unknown"
```

---

## 📊 テスト結果

### テストケース1: バージョン表示

```bash
$ python main.py --version
c-test-gen 2.4.4
```

✅ **成功**: VERSIONファイルから正しく読み込み

### テストケース2: 標準型読み込み

```bash
$ python main.py -i 22_難読化_obfuscated.c -f Utf1 -o test_v244
[INFO] 2025-11-19 00:47:27 - src.parser.typedef_extractor - standard_types.hから34個の標準型を読み込みました
```

✅ **成功**: 34個の標準型を正常に読み込み

### テストケース3: 警告チェック

```bash
$ python main.py ... 2>&1 | grep -i "warning.*int8_t"
(出力なし)
```

✅ **成功**: 標準型に関する警告なし（従来は出力されていた）

---

## 🔄 マイグレーション

### v2.4.3.1からの移行

1. **必須ファイル**:
   - `standard_types.h` をプロジェクトルートに配置
   - `VERSION` ファイルが存在することを確認

2. **コード変更**: なし（自動的に新機能が有効化）

3. **動作確認**:
   ```bash
   python main.py --version  # バージョン表示
   python main.py -i sample.c -f func -o output  # 通常動作
   ```

---

## 📝 既知の問題

なし

---

## 🚀 次のバージョン予定

### v2.5.0（タスク3）

- MC/DC 100%達成のためのpcpp統合
- プリプロセッサディレクティブの完全展開
- より多くの条件式抽出

---

## 📦 ファイル構成の変更

### 新規追加

- `standard_types.h` - 標準型定義ファイル

### 変更

- `src/parser/typedef_extractor.py` - 標準型の動的読み込み機能追加
- `src/cli.py` - バージョン動的取得機能追加
- `VERSION` - 2.4.3.1 → 2.4.4

---

## 👥 貢献者

- ichiryu (開発・テスト)

---

## 📖 関連ドキュメント

- [HANDOFF_v2_4_3_1_INTEGRATED.md](./HANDOFF_v2_4_3_1_INTEGRATED.md) - 統合引継ぎ資料
- [CLASS_DIAGRAM_v2_4_3.md](./CLASS_DIAGRAM_v2_4_3.md) - クラス図
- [SEQUENCE_DIAGRAM_v2_4_3.md](./SEQUENCE_DIAGRAM_v2_4_3.md) - シーケンス図
