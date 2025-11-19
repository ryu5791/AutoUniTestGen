# AutoUniTestGen v2.6.0 リリースノート

**リリース日**: 2025-11-19  
**重要度**: 🔴 **Critical** - MC/DCカバレッジの重大な改善

---

## 🎯 概要

v2.6.0では、ネストしたAND/OR条件のMC/DC真偽表生成を完全にサポートし、MC/DC 100%カバレッジを達成しました。これにより、複雑な条件分岐を持つ組込みシステムのコードにも完全対応します。

---

## ✨ 新機能

### 1. ネストしたAND/OR条件の完全サポート

**問題**:
従来のバージョンでは、以下のような複雑なネスト構造を持つ条件の真偽表生成が不完全でした:

```c
if ((A == value1) &&
    ((B == 1) || (B == 2) || (B == 3) || (B == 6) || (B == 7) || (B == 8)) &&
    (C == 0)) {
    // 処理
}
```

上記の条件では:
- トップレベル: 3つのAND条件
- 中間レベル: 6つのOR条件がネスト

**改善内容**:

1. **再帰的なOR/AND条件展開**
   - ネストした条件を再帰的に展開し、全ての単純条件を抽出
   - 例: `((B==1)||(B==2)||(B==3))` → `[B==1, B==2, B==3]`

2. **MC/DCパターン生成の改善**
   - 各単純条件の独立性を正しくテスト
   - ORグループ内の各条件を1つずつ真にするパターンを生成
   - ANDトップレベルでの適切なベースパターン生成

3. **期待される真偽表の生成**
   ```
   TTFFFFFT - 条件A=T, ORグループの1番目=T, 条件C=T
   FTFFFFFT - 条件A=F, ORグループの1番目=T, 条件C=T (Aの独立性)
   TFFFFFFT - 条件A=T, ORグループ全てF, 条件C=T (ORグループの独立性)
   TTFFFFFF - 条件A=T, ORグループの1番目=T, 条件C=F (Cの独立性)
   TFTFFFFT - 条件A=T, ORグループの2番目=T, 条件C=T
   TFFTFFFT - 条件A=T, ORグループの3番目=T, 条件C=T
   TFFFTFFT - 条件A=T, ORグループの4番目=T, 条件C=T
   TFFFFTFT - 条件A=T, ORグループの5番目=T, 条件C=T
   TFFFFFTT - 条件A=T, ORグループの6番目=T, 条件C=T
   ```

---

## 🔧 主な変更点

### MCDCPatternGenerator (src/truth_table/mcdc_pattern_generator.py)

**追加されたメソッド**:
- `generate_mcdc_patterns_for_complex()`: ネスト条件のMC/DCパターン生成
- `_extract_or_conditions()`: OR条件の再帰的展開
- `_extract_and_conditions()`: AND条件の再帰的展開
- `_generate_patterns_for_structure()`: 条件構造に基づくパターン生成
- `_generate_or_group_patterns_with_structure()`: ORグループのパターン生成（構造考慮）
- `_create_base_pattern_for_and()`: ANDベースパターン作成

**改善されたアルゴリズム**:
```python
# Before (v2.5.0以前)
# 2つずつの条件しか扱えない
if n_conditions == 2:
    return ['TF', 'FT', 'FF']  # OR
    
# After (v2.6.0)
# ネスト構造を再帰的に展開して全条件を処理
expanded_conditions = self._extract_or_conditions(nested_condition)
# → ['cond1', 'cond2', 'cond3', 'cond4', 'cond5', 'cond6']
```

### ConditionAnalyzer (src/truth_table/condition_analyzer.py)

**強化された分析機能**:
```python
def _analyze_and_condition(self, condition: Condition) -> Dict:
    # ネスト構造を検出
    has_nested = any('||' in cond or '&&' in cond for cond in conditions)
    
    if has_nested:
        # 新しいメソッドを使用
        patterns = mcdc_gen.generate_mcdc_patterns_for_complex('and', conditions)
    else:
        # 従来のメソッド
        patterns = mcdc_gen.generate_and_patterns(n_conditions)
```

---

## 📊 パフォーマンス

### テストケース

**入力コード**:
```c
if ((Utx104.Utm11.Utm14 == UtD27) &&
    ((UtD39 == 1) || (UtD39 == 2) || (UtD39 == 3) ||
     (UtD39 == 6) || (UtD39 == 7) || (UtD39 == 8)) &&
    (UtD38 == 0)) {
    UtD38 = 1;
}
```

**結果**:
| 項目 | v2.5.0 | v2.6.0 | 改善 |
|------|--------|--------|------|
| 展開された条件数 | 3個 | 8個 | ✅ +5個 |
| 生成されたパターン数 | 4個 | 9個 | ✅ +5個 |
| MC/DCカバレッジ | 約44% | **100%** | ✅ +56% |
| 期待パターン一致率 | 0/9 | **9/9** | ✅ 完璧 |

---

## 🐛 修正されたバグ

### Issue #1: ネストしたOR条件が展開されない

**症状**:
```
((B==1)||(B==2)||(B==3)||(B==4)||(B==5)||(B==6))
```
↓ v2.5.0では
```
展開後: 1個の条件として扱われる
```

**修正後** (v2.6.0):
```
展開後: [B==1, B==2, B==3, B==4, B==5, B==6] (6個)
```

### Issue #2: MC/DCパターン生成の不完全性

**症状**:
3つ以上のAND条件で、中間にORグループがある場合に、各OR条件の独立性テストが生成されない。

**修正後**:
各OR条件の独立性を個別にテストするパターンを生成。

---

## 🔄 後方互換性

### 既存の機能への影響

✅ **完全に後方互換**
- 既存の`generate_or_patterns()`、`generate_and_patterns()`は維持
- 新しいメソッドは追加のみで、既存メソッドは変更なし
- 単純な条件(2-3個のOR/AND)では従来のメソッドを使用

### アップグレードパス

```bash
# v2.5.0からv2.6.0へのアップグレード
git pull
# または
tar -xzf AutoUniTestGen_v2_6_0.tar.gz

# 設定変更不要 - そのまま使用可能
python main.py -i source.c -f function_name -o output
```

---

## 📝 使用例

### 基本的な使用方法

```bash
# ネストした条件を含むCファイルを処理
python main.py -i complex_code.c -f target_function -o output/

# 生成されるファイル:
#   - output/target_function_truth_table.xlsx  (9パターン)
#   - output/target_function_test.c
#   - output/target_function_io_table.xlsx
```

### プログラムからの使用

```python
from src.parser.c_code_parser import CCodeParser
from src.truth_table.truth_table_generator import TruthTableGenerator

# Cコードを解析
parser = CCodeParser()
parsed_data = parser.parse('source.c', target_function='func')

# 真偽表を生成 (ネスト条件も自動対応)
truth_gen = TruthTableGenerator()
truth_table = truth_gen.generate(parsed_data)

# 結果: MC/DC 100%のパターンが生成される
print(f"生成されたパターン数: {len(truth_table.test_cases)}")
```

---

## ⚠️ 既知の制限事項

1. **極端に深いネスト**: 10階層以上のネストは未テスト
2. **混在した演算子優先度**: `A || B && C || D`のような複雑な優先度は追加テストが必要

---

## 🔮 次期バージョン (v2.7.0) の予定

1. **パフォーマンス最適化**
   - 大規模ファイル (10,000行以上) の処理速度向上
   - メモリ使用量の削減

2. **テストコード生成の改善**
   - ネストした条件に対応した変数初期化コードの生成
   - より詳細なコメントの自動生成

3. **ドキュメント強化**
   - ネストした条件のベストプラクティス
   - トラブルシューティングガイド

---

## 👥 貢献者

- **ichiryu** - メイン開発者

---

## 📞 サポート

質問や問題がある場合:
1. GitHubのIssueを作成
2. プロジェクトのディスカッションフォーラムを利用

---

## 📜 ライセンス

このプロジェクトは MIT License の下で公開されています。

---

**感謝**: このバージョンは、複雑な組込みシステムコードの単体テスト自動化というユーザーの要求に応えるために開発されました。MC/DC 100%カバレッジの達成は、重要なマイルストーンです。
